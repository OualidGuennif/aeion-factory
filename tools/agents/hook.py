#!/usr/bin/env python3
# Spec: knowledge/operations/agent-compatibility.md
"""Adapt native Codex/OpenCode/Devin/Droid/Antigravity payloads to existing guards and verified handovers."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/context'))
import budget

# Devin names its native tools in lowercase; the shared guards use Claude's names.
DEVIN_TOOLS = {'exec': 'Bash', 'bash': 'Bash', 'shell': 'Bash', 'read': 'Read', 'grep': 'Grep',
               'edit': 'Edit', 'write': 'Write'}
# Factory's Droid sends Claude-shaped payloads with its own names for the shell, create and patch tools.
DROID_TOOLS = {'Execute': 'Bash', 'Create': 'Write', 'ApplyPatch': 'apply_patch'}
DROID_KNOWN = {*DROID_TOOLS, 'Bash', 'Read', 'Edit', 'MultiEdit', 'Write', 'Grep', 'Glob', 'LS'}
# Antigravity nests the call as toolCall {name, args}. Its own tools use PascalCase arguments, MCP tools any
# case; an argument at any depth named like a path, file, directory or URI (AbsolutePath, TargetDirectories,
# file_path, Uri) names files for the guards.
ANTIGRAVITY_TOOLS = {'run_command': 'Bash', 'view_file': 'Read', 'write_to_file': 'Write',
                     'replace_file_content': 'Edit', 'multi_replace_file_content': 'Edit', 'grep_search': 'Grep'}
ANTIGRAVITY_PATH_KEY = re.compile(r'(paths?|files?|dirs?|directory|directories|uris?)$')
# view_code_item's NodePaths are code symbols (Cache.key), not files.
ANTIGRAVITY_SYMBOL_KEYS = {'nodepath', 'nodepaths'}
# An argument at any depth named like a file filter (Includes, glob, IncludePattern, file_pattern) picks files to read.
ANTIGRAVITY_GLOB_KEY = re.compile(r'(includes?|globs?|patterns?)$')


class GuardRefusal(ValueError):
    """A known guard verdict, safe to return without echoing the input payload."""


def key(provider, event):
    value = event.get('session_id')
    # Devin and Antigravity document no session id; one key per clone keeps the guards on instead of refusing everything.
    if provider in {'devin', 'antigravity'} and value is None:
        return provider + '-local-' + hashlib.sha256(str(ROOT).encode()).hexdigest()[:16]
    if not isinstance(value, str) or not value or len(value) > 200:
        raise ValueError('a bounded native session identifier is required')
    return provider + '-' + hashlib.sha256(value.encode()).hexdigest()[:40]


def fail(provider, name, reason):
    # Devin's block on Stop means "keep going", so only a tool call is refused that way.
    if provider == 'devin' and name == 'PreToolUse':
        return {'decision': 'block', 'reason': reason}
    if provider == 'antigravity' and name == 'PreToolUse':
        return {'decision': 'deny', 'reason': reason}
    if name == 'PreToolUse':
        return {'hookSpecificOutput': {'hookEventName': name, 'permissionDecision': 'deny',
                                       'permissionDecisionReason': reason}}
    return {'continue': False, 'stopReason': reason, 'systemMessage': reason}


def advisory(root, event):
    """Token feedback reads the transcript when the harness passes a known shape; it may fail, never stop work."""
    try:
        return script(root, 'token-feedback.py', event)
    except Exception:  # noqa: BLE001 - a timeout or crash here must not become a continue: false.
        return {}


def script(root, name, event):
    result = subprocess.run([sys.executable, str(root / '.claude/hooks' / name)], cwd=root,
                            input=json.dumps(event), capture_output=True, text=True, timeout=4)
    if result.returncode == 2:
        raise GuardRefusal((result.stderr or 'Æion Factory check refused this action')[:1500])
    if result.returncode:
        raise ValueError('Æion Factory checker failed')
    if name == 'session-start.py':
        return {'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': result.stdout.strip()}}
    return json.loads(result.stdout) if result.stdout.lstrip().startswith('{') else {}


def edit_paths(event, provider=None):
    data = event.get('tool_input', {})
    if not isinstance(data, dict):
        raise ValueError('tool_input must be an object')
    if event.get('tool_name') == 'apply_patch':
        patch = next((data[field] for field in ('command', 'patchText', 'patch', 'input') if field in data), None)
        if not isinstance(patch, str):
            raise ValueError('apply_patch requires its native patch string')
        paths = re.findall(r'^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+)$', '\n'.join(patch.splitlines()), re.M)
        if not paths:
            raise ValueError('apply_patch has no recognized file paths')
        return paths
    if provider == 'antigravity':
        paths = event['antigravity_paths']
    else:
        path = data.get('file_path', data.get('filePath', data.get('path')))
        paths = [path] if path is not None else []
    if not paths and event.get('tool_name') in {'Read', 'Edit', 'Write'}:
        raise ValueError('the native file tool requires its supported path field')
    return paths


def argument_name(key):
    return re.sub(r'[_-]', '', str(key)).lower()


def antigravity_paths(value, named=False):
    # A string is a path only under a path-like name; nested objects and lists are walked.
    if isinstance(value, dict):
        paths = []
        for key, item in value.items():
            name = argument_name(key)
            path_like = ANTIGRAVITY_PATH_KEY.search(name) is not None and name not in ANTIGRAVITY_SYMBOL_KEYS
            paths += antigravity_paths(item, named or path_like)
        return paths
    if isinstance(value, list):
        return [path for item in value for path in antigravity_paths(item, named)]
    if named and isinstance(value, str) and value:
        # A file URI may carry a fragment, a query or percent-encoding; only its decoded path names the file.
        return [unquote(urlsplit(value).path) if value[:5].lower() == 'file:' else value]
    return []


def antigravity_globs(value, named=False):
    # Walked like paths: a string is a file filter only under a filter-like name, and anything else there is refused.
    if isinstance(value, dict):
        return [glob for key, item in value.items()
                for glob in antigravity_globs(item, named or ANTIGRAVITY_GLOB_KEY.search(argument_name(key)) is not None)]
    if isinstance(value, list):
        return [glob for item in value for glob in antigravity_globs(item, named)]
    if named and not isinstance(value, str):
        raise ValueError('the Antigravity include patterns must be strings')
    return [value] if named and value else []


def antigravity_event(event):
    call = event.get('toolCall')
    if call is None:
        # A pre-tool payload without the documented call shape has nothing to guard, so it is not allowed blind.
        if event.get('hook_event_name') == 'PreToolUse':
            raise ValueError('the Antigravity pre-tool payload requires a toolCall')
        return {**event, 'antigravity_paths': []}
    if not isinstance(call, dict) or not isinstance(call.get('args'), dict):
        raise ValueError('the Antigravity toolCall requires an args object')
    args = call['args']
    # The guards see only what the adapter derives, so a model-supplied limit or output mode cannot widen them.
    data = {}
    # A command line under any case (CommandLine, command_line, command) is a shell call, as for Devin and Droid.
    commands = [value for key, value in args.items() if argument_name(key) in {'commandline', 'command'}]
    if len(commands) > 1:
        raise ValueError('the Antigravity call names more than one command line')
    command = commands[0] if commands else None
    if command is not None:
        data['command'] = command
    # The shell's directory under any case (Cwd, cwd, workdir) sizes relative reads where they run.
    workdirs = [value for key, value in args.items() if argument_name(key) in {'cwd', 'workdir'}]
    if len(workdirs) > 1:
        raise ValueError('the Antigravity call names more than one working directory')
    if workdirs and not isinstance(workdirs[0], str):
        raise ValueError('the Antigravity working directory must be a string')
    if workdirs:
        data['workdir'] = unquote(urlsplit(workdirs[0]).path) if workdirs[0][:5].lower() == 'file:' else workdirs[0]
    # The guard cannot know which other argument a shell tool runs in, so on a shell call every argument
    # besides the command and its directory must be a flag or a number (run_command's Blocking, WaitMsBeforeAsync).
    if command is not None and any(argument_name(key) not in {'commandline', 'command', 'cwd', 'workdir'}
                                   and not isinstance(value, (bool, int, float)) for key, value in args.items()):
        raise ValueError('the Antigravity shell call carries an argument the guards cannot place')
    # Every path-like argument meets the guards, not only the first: one call can name several files.
    paths = antigravity_paths(args)
    # grep_search's Includes and any tool's file filters pick the files it reads, so each meets the Grep glob check.
    globs = antigravity_globs(args)
    # view_file windows by StartLine/EndLine; the intake guard reads the same window as offset/limit.
    if type(args.get('StartLine')) is int and type(args.get('EndLine')) is int:
        data['offset'], data['limit'] = args['StartLine'], args['EndLine'] - args['StartLine'] + 1
    # grep_search with MatchPerLine false lists file names only, which needs no intake limit.
    if args.get('MatchPerLine') is False:
        data['output_mode'] = 'files_with_matches'
    tool = ANTIGRAVITY_TOOLS.get(call.get('name'), call.get('name'))
    # Any tool carrying a command line is a shell call; a file path in it still meets the path guard.
    if command is not None:
        tool = 'Bash'
    return {**event, 'tool_name': tool, 'tool_input': data, 'antigravity_paths': paths, 'antigravity_globs': globs}


def handle(root, provider, event):
    if provider not in {'codex', 'opencode', 'devin', 'droid', 'antigravity'} or not isinstance(event, dict):
        raise ValueError('invalid provider or event')
    if provider == 'antigravity':
        event = antigravity_event(event)
    if provider == 'devin':
        tool = str(event.get('tool_name', '')).lower()
        data = event.get('tool_input')
        # An unknown Devin tool that carries a command string is a shell call until proven otherwise.
        if tool not in DEVIN_TOOLS and tool != 'apply_patch' and isinstance(data, dict) and isinstance(data.get('command'), str):
            tool = 'exec'
        if tool in DEVIN_TOOLS or tool == 'apply_patch':
            event = {**event, 'tool_name': DEVIN_TOOLS.get(tool, tool)}
    if provider == 'droid':
        tool = event.get('tool_name')
        data = event.get('tool_input')
        # Droid's tool names are not live-verified, so an unknown tool carrying a command string is a shell call.
        if tool not in DROID_KNOWN and isinstance(data, dict) and isinstance(data.get('command'), str):
            tool = 'Execute'
        if tool in DROID_TOOLS:
            event = {**event, 'tool_name': DROID_TOOLS[tool]}
    name = event.get('hook_event_name')
    if name not in {'SessionStart', 'PreToolUse', 'PostToolUse', 'PreCompact', 'Stop'}:
        raise ValueError('unsupported adapter event')
    session = key(provider, event)
    normalized = {**event, 'session_id': session}
    with budget.locked(root, session) as file:
        state = json.loads(file.read_text()) if file.exists() else {'epoch': 0, 'state': 'RUNNING', 'profile': provider}
        handover = budget.handover_path(root, session)
        if state.get('state') == 'STOPPED':
            return fail(provider, name, 'Æion Factory session is stopped; use its handover in a new session.')
        if name == 'SessionStart' and event.get('source') == 'compact':
            state.pop('checkpoint', None)
            state['epoch'] += 1
        budget.atomic(file, json.dumps(state, sort_keys=True) + '\n')
        if name == 'PreCompact':
            if not budget.ready(root, session, state):
                budget.ensure_handover(root, session)
                return fail(provider, name, f'Fill {handover.relative_to(root)} and verify the docs before compaction: '
                            + budget.checkpoint_command(root, session))
            if provider == 'opencode':
                state.pop('checkpoint', None)
                budget.atomic(file, json.dumps(state, sort_keys=True) + '\n')
            return {'systemMessage': f'Æion Factory verified handover: {handover.relative_to(root)}'}
    if name == 'SessionStart':
        result = script(root, 'session-start.py', normalized)
        pointer = 'Handover' if handover.is_file() else 'Handover (created at the first refused compaction)'
        context = (f'Æion Factory {provider} checkpoint profile. {pointer}: {handover.relative_to(root)}. '
                   f'Checkpoint key: {session}. Native token-stop enforcement is unqualified; do not claim a strict 300k cap.')
        if provider in {'devin', 'droid', 'antigravity'}:
            context = f'Æion Factory {provider} profile: shared guards and edit feedback; no compaction checkpoint or token stop.'
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
            # An unknown tool routed here may also name a file; that path still meets the path guard.
            for path in edit_paths(event, provider):
                script(root, 'guard-path.py', {'tool_name': 'Edit', 'tool_input': {**data, 'file_path': path}})
            return result
        for pattern in event.get('antigravity_globs', []) if provider == 'antigravity' else []:
            script(root, 'guard-path.py', {'tool_name': 'Grep', 'tool_input': {'glob': pattern}})
        paths = edit_paths(event, provider)
        if not paths and event.get('tool_name') == 'Grep':
            script(root, 'guard-path.py', normalized)
        for path in paths:
            tool = 'Edit' if event.get('tool_name') == 'apply_patch' else event.get('tool_name')
            data = {**event['tool_input'], 'file_path': path}
            script(root, 'guard-path.py', {'tool_name': tool, 'tool_input': data})
        return {}
    if name == 'PostToolUse':
        messages = []
        edited = edit_paths(event, provider) if event.get('tool_name') in {'apply_patch', 'Edit', 'Write'} else []
        for raw in edited:
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
        context = advisory(root, normalized).get('hookSpecificOutput', {}).get('additionalContext')
        if context:
            messages.append(context)
        return {'hookSpecificOutput': {'hookEventName': name, 'additionalContext': '\n'.join(messages)}} if messages else {}
    if name == 'Stop':
        advisory(root, normalized)
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
    except (ValueError, OSError, RecursionError):
        print('Æion Factory hook payload invalid or oversized; action refused.', file=sys.stderr)
        return 2
    provider = sys.argv[1] if len(sys.argv) > 1 else None
    # Antigravity's payload names no hook event, so its registration passes the event as an argument.
    if provider == 'antigravity':
        event['hook_event_name'] = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        result = handle(ROOT, provider, event)
        # Antigravity reads a pre-tool answer without a decision as a refusal, so an allowed call says so.
        if provider == 'antigravity' and event['hook_event_name'] == 'PreToolUse' and 'decision' not in result:
            result = {'decision': 'allow'}
    except GuardRefusal as error:
        result = fail(provider, event.get('hook_event_name'), str(error))
    except (ValueError, KeyError, IndexError, TypeError, OSError, RecursionError, subprocess.SubprocessError):
        name = event.get('hook_event_name') if isinstance(event, dict) else None
        result = fail(provider, name, 'Æion Factory adapter verification unavailable; resolve the hook/check error before continuing.')
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    sys.exit(main())
