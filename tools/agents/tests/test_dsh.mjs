import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { apply, inject } from '../../../.dsh/plugins/factory/index.js';
import * as compaction from '../../../.dsh/plugins/factory/compaction.js';
import { seam } from '../../../.dsh/plugins/factory/seam.js';

const root = fileURLToPath(new URL('../../../', import.meta.url));
const sessionID = `factory-dsh-plugin-test-${process.pid}`;

// A stand-in for the dsh Cordis context: it records the guard, the listeners and compactions. `meter.tokens`
// can change between calls; `root: false` is a profile without a root compaction service (web).
function load(cwd, totalTokens = 1000, { root: service = true } = {}) {
  const meter = { tokens: totalTokens };
  const handlers = {};
  const guards = [];
  const compactions = [];
  const ctx = {
    tools: { guard: (guard) => guards.push(guard) },
    tokenMeter: { measure: () => ({ totalTokens: meter.tokens }) },
    compaction: { compactIfNeeded: async (agent, trigger) => compactions.push(trigger) },
    on: (name, handler) => { handlers[name] = handler; },
    logger: { warn: () => {} },
  };
  const previous = process.cwd();
  process.chdir(cwd);
  seam.compaction = undefined;
  try {
    apply(ctx);
    if (service) compaction.apply(ctx);
  } finally {
    process.chdir(previous);
  }
  const steered = [];
  const agent = { session: { id: sessionID }, steer: (message) => steered.push(message) };
  return { handlers, guard: guards[0], compactions, agent, steered, meter };
}

const call = (agent, name, args) => ({ name, arguments: args, agent, callId: 'call-1' });

test('dsh registers one guard and the step and result listeners', () => {
  const { handlers, guard } = load(root);
  // The guards wait for no compaction service: dsh web keeps it inside each agent preset.
  assert.deepEqual(inject, ['tools', 'tokenMeter']);
  assert.deepEqual(compaction.inject, ['compaction']);
  assert.equal(typeof guard, 'function');
  assert.deepEqual(Object.keys(handlers).sort(), ['agent/pre-step', 'tools/post-execute']);
});

test('dsh tool calls that read a secret are denied before execution', () => {
  const { guard, agent } = load(root);
  assert.match(guard(call(agent, 'bash', { command: 'cat .env' })), /secret|Æion/);
  assert.ok(guard(call(agent, 'read', { file_path: `${root}/.env` })));
  assert.equal(guard(call(agent, 'bash', { command: 'git status --short' })), undefined);
});

test('dsh refuses a call that has no agent to account it to', () => {
  const { guard } = load(root);
  assert.match(guard({ name: 'bash', arguments: { command: 'true' } }), /unavailable/);
});

test('dsh past 250k is held to closure by its own token meter', () => {
  const { guard, agent } = load(root, 260000);
  agent.session.id = `${sessionID}-250k`;
  assert.match(guard(call(agent, 'write', { file_path: `${root}/src.py`, content: 'x' })), /250k alert/);
});

test('dsh compacts before the next step once the hook reports a verified handover, then resumes', async () => {
  // A stand-in adapter answers as the shared rule does after a verified checkpoint past 250k.
  const folder = mkdtempSync(join(tmpdir(), 'dsh-compact-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), 'import json\nprint(json.dumps({"aeion": {"compact": True}}))\n');
  const { handlers, compactions, agent, steered } = load(folder, 260000);
  const done = { kind: 'accept' };
  assert.equal(await handlers['tools/post-execute'](call(agent, 'bash', { command: 'true' }), {}, async () => done), done);
  let stepped = 0;
  await handlers['agent/pre-step']({ agent, signal: new AbortController().signal }, async () => { stepped += 1; });
  // Only once: the next step runs without compacting again.
  await handlers['agent/pre-step']({ agent, signal: new AbortController().signal }, async () => { stepped += 1; });
  rmSync(folder, { recursive: true, force: true });
  assert.deepEqual(compactions, ['context-overflow']);
  assert.equal(stepped, 2);
  assert.equal(steered.length, 1);
  assert.match(steered[0].content[0].text, /handover/);
});

// A stand-in adapter that records the events it receives and asks for a compaction after each tool.
function recorder() {
  const folder = mkdtempSync(join(tmpdir(), 'dsh-record-'));
  mkdirSync(join(folder, 'tools/agents'), { recursive: true });
  writeFileSync(join(folder, 'tools/agents/hook.py'), [
    'import json, sys',
    'event = json.load(sys.stdin)',
    "open('events.jsonl', 'a').write(json.dumps(event) + '\\n')",
    'print(json.dumps({"aeion": {"compact": True}}))',
  ].join('\n') + '\n');
  const events = () => readFileSync(join(folder, 'events.jsonl'), 'utf8').trim().split('\n').map(JSON.parse);
  return { folder, events };
}

test('dsh without a root compaction service asks the user for /compact instead of compacting', async () => {
  const { folder } = recorder();
  const { handlers, compactions, agent, steered } = load(folder, 260000, { root: false });
  agent.session.id = `${sessionID}-web`;
  await handlers['tools/post-execute'](call(agent, 'bash', { command: 'true' }), {}, async () => ({}));
  let stepped = 0;
  await handlers['agent/pre-step']({ agent, signal: new AbortController().signal }, async () => { stepped += 1; });
  rmSync(folder, { recursive: true, force: true });
  assert.deepEqual(compactions, []);
  assert.equal(stepped, 1);
  assert.equal(steered.length, 1);
  assert.match(steered[0].content[0].text, /\/compact/);
});

test('dsh treats a token fall to under half as a compaction and restarts the session as compacted', () => {
  const { folder, events } = recorder();
  const { guard, agent, meter } = load(folder, 260000, { root: false });
  agent.session.id = `${sessionID}-fall`;
  guard(call(agent, 'bash', { command: 'true' }));
  meter.tokens = 40000;
  guard(call(agent, 'bash', { command: 'true' }));
  // A small rise afterwards is no new compaction.
  meter.tokens = 41000;
  guard(call(agent, 'bash', { command: 'true' }));
  const starts = events().filter((event) => event.hook_event_name === 'SessionStart').map((event) => event.source);
  rmSync(folder, { recursive: true, force: true });
  assert.deepEqual(starts, ['startup', 'compact']);
});
