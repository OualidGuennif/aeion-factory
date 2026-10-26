#!/usr/bin/env python3
# Spec: knowledge/operations/agent-compatibility.md
"""Adapt native Codex/OpenCode payloads to existing guards and verified handovers."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/context'))
import budget


class GuardRefusal(ValueError):
    """A known guard verdict, safe to return without echoing the input payload."""


def key(provider, event):
    value = event.get('session_id')
    if not isinstance(value, str) or not value or len(value) > 200:
        raise ValueError('a bounded native session identifier is required')
    return provider + '-' + hashlib.sha256(value.encode()).hexdigest()[:40]


def fail(name, reason):
    if name == 'PreToolUse':
        return {'hookSpecificOutput': {'hookEventName': name, 'permissionDecision': 'deny',
                                       'permissionDecisionReason': reason}}
    return {'continue': False, 'stopReason': reason, 'systemMessage': reason}


def script(root, name, event):
    result = subprocess.run([sys.executable, str(root / '.claude/hooks' / name)], cwd=root,
                            input=json.dumps(event), capture_output=True, text=True, timeout=4)
    if result.returncode == 2:
        raise GuardRefusal((result.stderr or 'Factory check refused this action')[:1500])
    if result.returncode:
        raise ValueError('Factory checker failed')
    if name == 'session-start.py':
        return {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': result.stdout.strip()}}
    return json.loads(result.stdout) if result.stdout.lstrip().startswith('{') else {}


def edit_paths(event):
    data = event.get('tool_input', {})
    if not isinstance(data, dict):
        raise ValueError('tool_input must be an object')
    if event.get('tool_name') == 'apply_patch':
        patch = data.get('command', data.get('patchText'))
        if not isinstance(patch, str):
            raise ValueError('apply_patch requires its native patch string')
        paths = re.findall(r'^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$', '\n'.join(patch.splitlines()), re.M)
        if not paths:
            raise ValueError('apply_patch has no recognized file paths')
        return paths
    path = data.get('file_path', data.get('filePath', data.get('path')))
    if path is None and event.get('tool_name') in {'Read', 'Edit', 'Write'}:
        raise ValueError('the native file tool requires its supported path field')
    return [path] if path is not None else []


def handle(root, provider, event):
    if provider not in {'codex', 'opencode'} or not isinstance(event, dict):
        raise ValueError('invalid provider or event')
    name = event.get('hook_event_name')
    if name not in {'SessionStart', 'PreToolUse', 'PostToolUse', 'PreCompact', 'Stop'}:
        raise ValueError('unsupported adapter event')
    session = key(provider, event)
    normalized = {**event, 'session_id': session}
    with budget.locked(root, session) as file:
        state = json.loads(file.read_text()) if file.exists() else {'epoch': 0, 'state': 'RUNNING', 'profile': provider}
        handover = budget.ensure_handover(root, session)
        if state.get('state') == 'STOPPED':
            return fail(name, 'Factory session is stopped; use its handover in a new session.')
        if name == 'SessionStart' and event.get('source') == 'compact':
            state.pop('checkpoint', None)
            state['epoch'] += 1
        budget.atomic(file, json.dumps(state, sort_keys=True) + '\n')
        if name == 'PreCompact':
            if not budget.ready(root, session, state):
                return fail(name, 'Verify the handover/docs before compaction: '
                            f'python3 tools/context/budget.py checkpoint --session {session} --base origin/main --verify')
            if provider == 'opencode':
                state.pop('checkpoint', None)
                budget.atomic(file, json.dumps(state, sort_keys=True) + '\n')
            return {'systemMessage': f'Factory verified handover: {handover.relative_to(root)}'}
    if name == 'SessionStart':
        result = script(root, 'session-start.py', normalized)
        context = (f'Factory {provider} checkpoint profile. Handover: {handover.relative_to(root)}. '
                   f'Checkpoint key: {session}. Native token-stop enforcement is unqualified; do not claim a strict 300k cap.')
        context += '\n' + result.get('hookSpecificOutput', {}).get('additionalContext', '')
        result['hookSpecificOutput'] = {'hookEventName': name, 'additionalContext': context}
        return result
    if name == 'PreToolUse':
        if event.get('tool_name') == 'Bash':
            data = event.get('tool_input')
            if not isinstance(data, dict) or not isinstance(data.get('command'), str) or not data['command'].strip():
                raise ValueError('the native Bash tool requires a nonempty command string')
            result = script(root, 'guard-bash.py', normalized)
            if result.get('hookSpecificOutput', {}).get('permissionDecision') == 'ask':
                return fail(name, 'This command requires an explicit human decision; the adapter does not auto-approve it.')
            return result
        for path in edit_paths(event):
            script(root, 'guard-path.py', {'tool_name': 'Read', 'tool_input': {'file_path': path}})
        return {}
    if name == 'PostToolUse' and event.get('tool_name') in {'apply_patch', 'Edit', 'Write'}:
        messages = []
        for raw in edit_paths(event):
            path = Path(raw)
            path = (root / path).resolve() if not path.is_absolute() else path.resolve()
            if not path.is_relative_to(root):
                continue
            with (Path(tempfile.gettempdir()) / f'claude-edited-{session}').open('a') as stream:
                stream.write(path.relative_to(root).as_posix() + '\n')
            result = script(root, 'after-edit.py', {**normalized, 'tool_input': {'file_path': str(path)}})
            context = result.get('hookSpecificOutput', {}).get('additionalContext')
            if context:
                messages.append(context)
        return {'hookSpecificOutput': {'hookEventName': name, 'additionalContext': '\n'.join(messages)}} if messages else {}
    if name == 'Stop':
        return script(root, 'sign-off.py', normalized)
    return {}


def main():
    event = {}
    try:
        event = json.loads(sys.stdin.read(2 * 1024 * 1024))
        result = handle(ROOT, sys.argv[1], event)
    except GuardRefusal as error:
        result = fail(event.get('hook_event_name'), str(error))
    except (ValueError, KeyError, IndexError, TypeError, OSError, subprocess.SubprocessError):
        name = event.get('hook_event_name') if isinstance(event, dict) else None
        result = fail(name, 'Factory adapter verification unavailable; resolve the hook/check error before continuing.')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
