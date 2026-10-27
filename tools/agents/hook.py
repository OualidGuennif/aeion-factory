#!/usr/bin/env python3
# Spec: knowledge/operations/agent-compatibility.md
"""Adapt native Codex/OpenCode/Devin payloads to existing guards and verified handovers."""
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

# Devin names its native tools in lowercase; the shared guards use Claude's names.
DEVIN_TOOLS = {'exec': 'Bash', 'bash': 'Bash', 'shell': 'Bash', 'read': 'Read', 'grep': 'Grep',
               'edit': 'Edit', 'write': 'Write'}


class GuardRefusal(ValueError):
    """A known guard verdict, safe to return without echoing the input payload."""


def key(provider, event):
    value = event.get('session_id')
    # Devin does not document a session id; one key per clone keeps the guards on instead of refusing everything.
    if provider == 'devin' and value is None:
        return 'devin-local-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
    if not isinstance(value, str) or not value or len(value) > 200:
        raise ValueError('a bounded native session identifier is required')
    return provider + '-' + hashlib.sha256(value.encode()).hexdigest()[:40]


def fail(provider, name, reason):
    # Devin's block on Stop means "keep going", so only a tool call is refused that way.
    if provider == 'devin' and name == 'PreToolUse':
        return {'decision': 'block', 'reason': reason}
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
    if provider not in {'codex', 'opencode', 'devin'} or not isinstance(event, dict):
        raise ValueError('invalid provider or event')
    if provider == 'devin':
        tool = str(event.get('tool_name', '')).lower()
        data = event.get('tool_input')
        # An unknown Devin tool that carries a command string is a shell call until proven otherwise.
        if tool not in DEVIN_TOOLS and tool != 'apply_patch' and isinstance(data, dict) and isinstance(data.get('command'), str):
            tool = 'exec'
        if tool in DEVIN_TOOLS:
            event = {**event, 'tool_name': DEVIN_TOOLS[tool]}
    name = event.get('hook_event_name')
    if name not in {'SessionStart', 'PreToolUse', 'PostToolUse', 'PreCompact', 'Stop'}:
        raise ValueError('unsupported adapter event')
    session = key(provider, event)
    normalized = {**event, 'session_id': session}
    with budget.locked(root, session) as file:
        state = json.loads(file.read_text()) if file.exists() else {'epoch': 0, 'state': 'RUNNING', 'profile': provider}
        handover = budget.handover_path(root, session)
        if state.get('state') == 'STOPPED':
            return fail(provider, name, 'Factory session is stopped; use its handover in a new session.')
        if name == 'SessionStart' and event.get('source') == 'compact':
            state.pop('checkpoint', None)
            state['epoch'] += 1
        budget.atomic(file, json.dumps(state, sort_keys=True) + '\n')
        if name == 'PreCompact':
            if not budget.ready(root, session, state):
                budget.ensure_handover(root, session)
                return fail(provider, name, f'Fill {handover.relative_to(root)} and verify the docs before compaction: '
                            f'python3 tools/context/budget.py checkpoint --session {session} --base origin/main --verify')
            if provider == 'opencode':
                state.pop('checkpoint', None)
                budget.atomic(file, json.dumps(state, sort_keys=True) + '\n')
            return {'systemMessage': f'Factory verified handover: {handover.relative_to(root)}'}
    if name == 'SessionStart':
        result = script(root, 'session-start.py', normalized)
        pointer = 'Handover' if handover.is_file() else 'Handover (created at the first refused compaction)'
        context = (f'Factory {provider} checkpoint profile. {pointer}: {handover.relative_to(root)}. '
                   f'Checkpoint key: {session}. Native token-stop enforcement is unqualified; do not claim a strict 300k cap.')
        if provider == 'devin':
            context = 'Factory devin profile: shared guards and edit feedback; no compaction checkpoint or token stop.'
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
                return fail(provider, name, 'This command requires an explicit human decision; the adapter does not auto-approve it.')
            return result
        paths = edit_paths(event)
        if not paths and event.get('tool_name') == 'Grep':
            script(root, 'guard-path.py', normalized)
        for path in paths:
            tool = 'Edit' if event.get('tool_name') == 'apply_patch' else event.get('tool_name')
            data = {**event['tool_input'], 'file_path': path}
            script(root, 'guard-path.py', {'tool_name': tool, 'tool_input': data})
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
    # Unknown-event failures need exit 2: native PreToolUse ignores generic stop fields.
    try:
        raw = sys.stdin.read(2 * 1024 * 1024 + 1)
        if len(raw) > 2 * 1024 * 1024:
            raise ValueError('oversized hook payload')
        event = json.loads(raw)
        if not isinstance(event, dict):
            raise ValueError('hook payload must be an object')
    except (ValueError, OSError):
        print('Factory hook payload invalid or oversized; action refused.', file=sys.stderr)
        return 2
    provider = sys.argv[1] if len(sys.argv) > 1 else None
    try:
        result = handle(ROOT, provider, event)
    except GuardRefusal as error:
        result = fail(provider, event.get('hook_event_name'), str(error))
    except (ValueError, KeyError, IndexError, TypeError, OSError, subprocess.SubprocessError):
        name = event.get('hook_event_name') if isinstance(event, dict) else None
        result = fail(provider, name, 'Factory adapter verification unavailable; resolve the hook/check error before continuing.')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
