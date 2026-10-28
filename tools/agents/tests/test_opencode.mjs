import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import plugin from '../../../.opencode/plugins/factory/index.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const hooks = {};
const register = (domain) => async (name, callback) => { hooks[`${domain}.${name}`] = callback; };
await plugin.setup({ location: { directory: root }, tool: { hook: register('tool') }, session: { hook: register('session') } });
const sessionID = `factory-v2-plugin-test-${process.pid}`;

test('OpenCode V2 registers native tool and compaction hooks', () => {
  assert.deepEqual(Object.keys(hooks).sort(), ['session.compaction', 'session.prompt', 'tool.execute.after', 'tool.execute.before']);
});

test('OpenCode V2 shell/read payloads refuse secrets before execution', async () => {
  await assert.rejects(hooks['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'cat .env' } }));
  await assert.rejects(hooks['tool.execute.before']({ tool: 'read', sessionID, input: { filePath: `${root}/.env` } }));
  await hooks['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'git status --short' } });
});

test('OpenCode V2 started in a subfolder finds the project hooks', async () => {
  const nested = {};
  const record = (domain) => async (name, callback) => { nested[`${domain}.${name}`] = callback; };
  await plugin.setup({ location: { directory: `${root}/demo` }, tool: { hook: record('tool') }, session: { hook: record('session') } });
  await nested['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'git status --short' } });
  await assert.rejects(nested['tool.execute.before']({ tool: 'shell', sessionID, input: { command: 'cat .env' } }), /secret/);
});

test('OpenCode V2 compaction refuses a missing checkpoint', async () => {
  const event = { sessionID, system: [] };
  await assert.rejects(hooks['session.compaction'](event), /checkpoint/);
  assert.deepEqual(event.system, []);
});
