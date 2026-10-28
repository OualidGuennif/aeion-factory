// Spec: knowledge/operations/agent-compatibility.md
import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const UNAVAILABLE = 'Æion Factory hook unavailable; action refused.';
// Pi's built-in tools under the names the shared guards know; find and ls only list paths.
const TOOLS = { bash: 'Bash', powershell: 'Bash', read: 'Read', edit: 'Edit', write: 'Write', grep: 'Grep', find: 'Glob', ls: 'LS' };

// Pi may start in a subfolder (demo/), so the hooks live in the nearest folder above that has them.
function projectRoot(directory) {
  for (let folder = resolve(directory); ; folder = dirname(folder)) {
    if (existsSync(resolve(folder, 'tools/agents/hook.py'))) return folder;
    if (dirname(folder) === folder) return directory;
  }
}

function invoke(root, event) {
  const result = spawnSync('python3', [resolve(root, 'tools/agents/hook.py'), 'pi'], {
    cwd: root, input: JSON.stringify(event), encoding: 'utf8', timeout: 15000, maxBuffer: 128 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error(UNAVAILABLE);
  const output = JSON.parse(result.stdout);
  const reason = output.stopReason || (output.decision === 'block' && output.reason)
    || (output.hookSpecificOutput?.permissionDecision === 'deny' && output.hookSpecificOutput.permissionDecisionReason);
  return { output, reason };
}

function toolEvent(event, ctx, name) {
  // An unknown tool that carries a command string is a shell call until proven otherwise.
  const shell = !(event.toolName in TOOLS) && typeof event.input?.command === 'string';
  return {
    session_id: ctx.sessionManager.getSessionId(), hook_event_name: name, tool_use_id: event.toolCallId,
    tool_name: shell ? 'Bash' : TOOLS[event.toolName] || event.toolName, tool_input: event.input,
  };
}

export default function (pi) {
  // Sessions given the factory's start context; a compaction removes one, so its next run is told again.
  const started = new Set();
  const compacted = new Set();

  pi.on('before_agent_start', async (event, ctx) => {
    const session = ctx.sessionManager.getSessionId();
    if (started.has(session)) return undefined;
    const source = compacted.has(session) ? 'compact' : 'startup';
    const { output, reason } = invoke(projectRoot(ctx.cwd), { session_id: session, hook_event_name: 'SessionStart', source });
    if (reason) throw new Error(reason);
    started.add(session);
    compacted.delete(session);
    const content = output.hookSpecificOutput?.additionalContext;
    return content ? { message: { customType: 'aeion-factory', content, display: false } } : undefined;
  });

  pi.on('tool_call', async (event, ctx) => {
    try {
      const { reason } = invoke(projectRoot(ctx.cwd), toolEvent(event, ctx, 'PreToolUse'));
      return reason ? { block: true, reason } : undefined;
    } catch (error) {
      return { block: true, reason: error.message || UNAVAILABLE };
    }
  });

  pi.on('tool_result', async (event, ctx) => {
    if (event.isError) return undefined;
    const { reason, output } = invoke(projectRoot(ctx.cwd), toolEvent(event, ctx, 'PostToolUse'));
    const message = reason || output.hookSpecificOutput?.additionalContext;
    if (!message) return undefined;
    return { content: [...event.content, { type: 'text', text: `Æion Factory feedback: ${message}` }], structuredContent: event.structuredContent };
  });

  pi.on('session_before_compact', async (event, ctx) => {
    const session = ctx.sessionManager.getSessionId();
    let reason;
    try {
      ({ reason } = invoke(projectRoot(ctx.cwd), { session_id: session, hook_event_name: 'PreCompact' }));
    } catch (error) {
      reason = error.message || UNAVAILABLE;
    }
    if (!reason) return undefined;
    ctx.ui.notify(reason, 'error');
    return { cancel: true };
  });

  pi.on('session_compact', async (event, ctx) => {
    started.delete(ctx.sessionManager.getSessionId());
    compacted.add(ctx.sessionManager.getSessionId());
  });
}
