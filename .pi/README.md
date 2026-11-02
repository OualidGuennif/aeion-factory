# Pi integration

Read the [setup runbook](../knowledge/operations/agent-compatibility.md).
Pi 1.4.0+ reads the root `AGENTS.md`/`CLAUDE.md` and the shared `.agents/skills` links from any folder
below the root; bodies are maintained once. The project extension in `extensions/factory/` reuses the
existing Python guards, edit checks and handover checkpoints through `tools/agents/hook.py pi`.

Launch with `tools/agents/run pi` and trust the project when Pi asks, so `.pi/extensions/` loads. Pi loads
project extensions from its start folder only: started elsewhere, pass it explicitly
(`pi -e ../.pi/extensions/factory/index.js` from `demo/`). The extension uses Node built-ins only.

It blocks a tool call on any refusal or hook failure, appends edit feedback to the tool result, gives
the factory context once per session and again after a compaction, and cancels a compaction without the
verified handover. The 250k alert names the checkpoint command, and closure admits a project's own
Markdown docs. Use the shared sign-off skill at task completion. Pi controls its own compaction
window (`compaction.reserveTokens`), but the extension compacts first: at 250k, once the handover is
verified, it calls `ctx.compact()` (headless `-p` currently fails at that call; see below); at 300k
only the handover and its checkpoint remain, and Pi compacts there whether or not the checkpoint
verifies. A settlement that still owes closure is continued at most
three times, then settles with the reason in the UI; any other terminal stop (`continue: false`) settles
at once with its reason shown, never as another request.

## Known limitation: headless 250k compaction (2026-11-02)

A live `pi -p` run (1.4.0) with 264,360 measured tokens hit the 250k gate and then failed: the
extension's `ctx.compact()` from `tool_result` aborts the run, its `onError` callback touches the
stale extension ctx (`This extension ctx is stale after session replacement or reload`), and the
process exits 1 with no compaction entry. `agent_before_settle` also sends Stop without
`observed_tokens`, so a text-only turn above 250k never triggers. Until fixed, do not rely on
headless 250k auto-compaction: keep the handover and checkpoint current and start a new session from
the handover. The guards and checkpoints still work; the interactive path was not re-tested.
