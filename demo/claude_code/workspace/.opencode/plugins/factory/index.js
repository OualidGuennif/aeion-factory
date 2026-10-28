// Spec: knowledge/operations/agent-compatibility.md
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

function invoke(root, event) {
  const result = spawnSync('python3', [resolve(root, 'tools/agents/hook.py'), 'opencode'], {
    cwd: root, input: JSON.stringify(event), encoding: 'utf8', timeout: 15000, maxBuffer: 128 * 1024,
  });
  if (result.error || result.status !== 0) throw new Error('Æion Factory hook unavailable; action refused.');
  const output = JSON.parse(result.stdout);
  const reason = output.stopReason || (output.decision === 'block' && output.reason)
    || (output.hookSpecificOutput?.permissionDecision === 'deny' && output.hookSpecificOutput.permissionDecisionReason);
  return { output, reason };
}

function toolEvent(event, name) {
  return {
    session_id: event.sessionID, hook_event_name: name,
    tool_use_id: event.id,
    tool_name: ({ bash: 'Bash', shell: 'Bash', read: 'Read', grep: 'Grep', edit: 'Edit', write: 'Write' })[event.tool] || event.tool,
    tool_input: event.input,
  };
}

export default {
  id: 'aeion.factory',
  async setup(ctx) {
    const root = ctx.location.directory;
    await ctx.session.hook('prompt', async (event) => {
      const { reason } = invoke(root, { session_id: event.sessionID, hook_event_name: 'SessionStart', source: 'startup' });
      if (reason) throw new Error(reason);
    });
    await ctx.tool.hook('execute.before', async (event) => {
      const { reason } = invoke(root, toolEvent(event, 'PreToolUse'));
      if (reason) throw new Error(reason);
    });
    await ctx.tool.hook('execute.after', async (event) => {
      if (event.status !== 'completed') return;
      const { reason, output } = invoke(root, toolEvent(event, 'PostToolUse'));
      const message = reason || output.hookSpecificOutput?.additionalContext;
      if (!message) return;
      const content = event.result.content;
      const parts = typeof content === 'string' ? [{ type: 'text', text: content }] : [...(content || [])];
      event.result = { ...event.result, content: [...parts, { type: 'text', text: `Æion Factory feedback: ${message}` }] };
    });
    await ctx.session.hook('compaction', async (event) => {
      const { reason, output } = invoke(root, { session_id: event.sessionID, hook_event_name: 'PreCompact' });
      if (reason) throw new Error(reason);
      event.system.push({ type: 'text', text: `${output.systemMessage}. Recover from this handover and read AGENTS.md.` });
    });
  },
};
