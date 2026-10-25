import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { FactoryPlugin } from '../../../.opencode/plugins/factory.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const client = { app: { log: async () => {} } };
const hooks = await FactoryPlugin({ worktree: root, directory: root, client });
const sessionID = `factory-plugin-test-${process.pid}`;

test('OpenCode native Bash and read payloads refuse secrets before execution', async () => {
  await assert.rejects(hooks['tool.execute.before']({ tool: 'bash', sessionID }, { args: { command: 'cat .env' } }));
  await assert.rejects(hooks['tool.execute.before']({ tool: 'read', sessionID }, { args: { filePath: `${root}/.env` } }));
  await hooks['tool.execute.before']({ tool: 'bash', sessionID }, { args: { command: 'git status --short' } });
});

test('OpenCode experimental compaction hook refuses a missing checkpoint', async () => {
  const output = { context: [] };
  await assert.rejects(hooks['experimental.session.compacting']({ sessionID }, output), /checkpoint/);
  assert.deepEqual(output.context, []);
});

test('OpenCode native lifecycle payloads initialize and retain a handover', async () => {
  await hooks.event({ event: { type: 'session.created', properties: { info: { id: sessionID } } } });
  await hooks.event({ event: { type: 'session.compacted', properties: { sessionID } } });
  await hooks.event({ event: { type: 'session.idle', properties: { sessionID } } });
});
