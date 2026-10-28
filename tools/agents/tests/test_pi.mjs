import test from 'node:test';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import extension from '../../../.pi/extensions/factory/index.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const sessionID = `factory-pi-extension-test-${process.pid}`;

// A stand-in for Pi's ExtensionAPI and ExtensionContext: it records handlers and notifications.
function load(cwd) {
  const handlers = {};
  const notes = [];
  extension({ on: (name, handler) => { handlers[name] = handler; } });
  const ctx = { cwd, sessionManager: { getSessionId: () => sessionID }, ui: { notify: (text, kind) => notes.push([kind, text]) } };
  return { handlers, notes, ctx };
}

const bash = (command) => ({ type: 'tool_call', toolCallId: 'call-1', toolName: 'bash', input: { command } });

test('Pi registers the start, tool and compaction events', () => {
  const { handlers } = load(root);
  assert.deepEqual(Object.keys(handlers).sort(),
    ['before_agent_start', 'session_before_compact', 'session_compact', 'tool_call', 'tool_result']);
});

test('Pi tool calls that read a secret are blocked before execution', async () => {
  const { handlers, ctx } = load(root);
  assert.equal((await handlers.tool_call(bash('cat .env'), ctx)).block, true);
  const read = { type: 'tool_call', toolCallId: 'call-2', toolName: 'read', input: { path: `${root}/.env` } };
  assert.equal((await handlers.tool_call(read, ctx)).block, true);
  assert.equal(await handlers.tool_call(bash('git status --short'), ctx), undefined);
});

test('Pi treats an unknown tool carrying a command as a shell call', async () => {
  const { handlers, ctx } = load(root);
  const custom = { type: 'tool_call', toolCallId: 'call-3', toolName: 'codemode_shell', input: { command: 'cat .env' } };
  assert.equal((await handlers.tool_call(custom, ctx)).block, true);
});

test('Pi started in a subfolder finds the project hooks', async () => {
  const { handlers, ctx } = load(`${root}/demo`);
  assert.equal(await handlers.tool_call(bash('git status --short'), ctx), undefined);
  assert.equal((await handlers.tool_call(bash('cat .env'), ctx)).block, true);
});

test('Pi compaction is cancelled without a verified checkpoint', async () => {
  const { handlers, notes, ctx } = load(root);
  assert.deepEqual(await handlers.session_before_compact({ type: 'session_before_compact', reason: 'threshold' }, ctx), { cancel: true });
  assert.match(notes[0][1], /checkpoint/);
});

test('Pi gives the factory context once per session, and again after a compaction', async () => {
  const { handlers, ctx } = load(root);
  const first = await handlers.before_agent_start({ type: 'before_agent_start', messageType: 'user', prompt: 'hi' }, ctx);
  assert.match(first.message.content, /Æion Factory pi checkpoint profile/);
  assert.equal(await handlers.before_agent_start({ type: 'before_agent_start', messageType: 'user', prompt: 'again' }, ctx), undefined);
  await handlers.session_compact({ type: 'session_compact', reason: 'manual' }, ctx);
  assert.ok(await handlers.before_agent_start({ type: 'before_agent_start', messageType: 'user', prompt: 'after' }, ctx));
});
