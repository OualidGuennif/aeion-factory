// Spec: knowledge/operations/agent-compatibility.md
import { spawnSync } from 'node:child_process';
import { resolve } from 'node:path';

export const FactoryPlugin = async ({ worktree, directory, client }) => {
  const root = worktree || directory;
  const invoke = (event) => {
    const result = spawnSync('python3', [resolve(root, 'tools/agents/hook.py'), 'opencode'], {
      cwd: root, input: JSON.stringify(event), encoding: 'utf8', timeout: 15000, maxBuffer: 128 * 1024,
    });
    if (result.error || result.status !== 0) throw new Error('Factory hook unavailable; action refused.');
    const output = JSON.parse(result.stdout);
    const reason = output.stopReason || (output.decision === 'block' && output.reason)
      || (output.hookSpecificOutput?.permissionDecision === 'deny' && output.hookSpecificOutput.permissionDecisionReason);
    return { output, reason };
  };
  const toolEvent = (input, args, name) => ({
    session_id: input.sessionID, hook_event_name: name,
    tool_name: ({ bash: 'Bash', read: 'Read', grep: 'Grep', edit: 'Edit', write: 'Write' })[input.tool] || input.tool,
    tool_input: args,
  });
  return {
    'tool.execute.before': async (input, output) => {
      const { reason } = invoke(toolEvent(input, output.args, 'PreToolUse'));
      if (reason) throw new Error(reason);
    },
    'tool.execute.after': async (input, toolOutput) => {
      const { reason, output } = invoke(toolEvent(input, input.args, 'PostToolUse'));
      const message = reason || output.hookSpecificOutput?.additionalContext;
      if (message) toolOutput.output += `\nFactory feedback: ${message}`;
    },
    'experimental.session.compacting': async (input, output) => {
      const { reason, output: checkpoint } = invoke({ session_id: input.sessionID, hook_event_name: 'PreCompact' });
      if (reason) throw new Error(reason);
      output.context.push(`${checkpoint.systemMessage}. Recover from this handover and read AGENTS.md.`);
    },
    event: async ({ event }) => {
      if (event.type === 'session.created') {
        invoke({ session_id: event.properties.info.id, hook_event_name: 'SessionStart', source: 'startup' });
      } else if (event.type === 'session.compacted') {
        invoke({ session_id: event.properties.sessionID, hook_event_name: 'SessionStart', source: 'compact' });
      } else if (event.type === 'session.idle') {
        const { output, reason } = invoke({ session_id: event.properties.sessionID, hook_event_name: 'Stop' });
        if (reason) await client.app.log({ body: { service: 'factory', level: 'warn', message: reason } });
      }
    },
  };
};
