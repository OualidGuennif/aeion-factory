---
type: Runbook
title: "Context safety and handover"
description: "Enabled Claude checkpoints, 250k native compaction, mandatory handovers, and the limits of 300k enforcement."
status: stable
generated:
  by: aeion-factory/1.1
  at: 2026-10-25
sources:
  - id: budget
    resource: ../../tools/context/budget.py
    title: "Budget state and documentation checkpoint"
  - id: hook
    resource: ../../.claude/hooks/context-budget.py
    title: "Claude hook adapter"
  - id: settings
    resource: ../../.claude/settings.json
    title: "Default registrations and compaction window"
  - id: tests
    resource: ../../tools/context/tests/test_budget.py
    title: "Boundary and failure regressions"
  - id: launcher
    resource: ../../tools/context/run
    title: "Managed launch and unsupported strict refusal"
---

# Context safety

[Bounded intake](../policies/bounded-intake.md) reduces obvious large Read/Grep/Bash dumps before
execution. Intake bounds are not output virtualization: no tool result is rewritten, and these
heuristics cannot establish an absolute context ceiling. Keep targeted reads and summary commands.

The default Claude profile enables native auto-compaction at 250,000 tokens and a budget hook
on session start, prompts, tools, compaction and stop. SubagentStop also checks a child's final
observation, including pure-text child responses. The hook reads only the current session's
bounded transcript tail and retains native token counts, never transcript text. Cached input
counts once. Missing or zero usage is unavailable, not an empty context. An incomplete final JSONL line is
a transient write; a malformed complete record is invalid.

Every event latches the first observed 250k crossing, including PreCompact. The hook alerts both
agent and user at the next supported event; PreCompact retains a pending alert because that event
discards system messages. Only closure work
(docs/task/handover edits and fixed verification commands) remains available. At an observed
300k it returns `continue: false`; a Stop reminder cannot override this decision. The session
state and active handover survive restart. Each session has its own file lock and atomic state.
Tool events carrying `agent_id` use a separate parent/agent key and that child's transcript,
including the documented nested `subagents/agent-<id>.jsonl` layout. Missing child usage refuses
the child; it never reads the parent's counters or changes the parent's stop state. Child
handover/checkpoint commands use the separate key printed by the guard.

Before any compaction, fill `work/handovers/<session-id>.md`, update `work/current.md` and affected
docs, and run `python3 tools/context/budget.py checkpoint --session <id> --base <git-ref> --verify`.
The command runs knowledge/link/health checks and binds readiness to the current source diff
and handover hash. Later edits invalidate it. Compaction is refused without a current receipt.
The skeleton appears only when closure needs it (the 250k alert, the observed stop, a refused
compaction or the first checkpoint command), so ordinary sessions and subagents leave none; replace each TODO. Keep outcomes, remaining
work, constraints and evidence concise. These local handovers are ignored by Git; durable facts
belong in Knowledge. After compaction the same file is the recovery pointer.

Startup and the first prompt allow a native bootstrap before usage exists. All later work
requires a positive native observation. A bounded retry waits for asynchronous transcript writes;
unavailable usage denies the current tool call (the agent keeps running and may retry it; other
events stop) without latching STOPPED, so a later valid observation
can recover. Invalid complete records and the observed 300k stop remain terminal. A `compact_boundary` or compact SessionStart clears the
old observation; resuming a stopped session does not clear its stop. Smaller model windows retain
their native earlier limit. The guard does not expand a model's capacity.

**Guarantee:** this is checkpoint-based enforcement, not a proof of an absolute 300k ceiling.
Claude Code exposes no qualified before-every-request admission callback here. A large tool
result or response may cross a threshold before another hook runs. `tools/context/run --strict`
therefore refuses execution rather than advertising unsupported strict protection. Codex/OpenCode support shared guards and verified checkpoints through their own adapters, with
token enforcement unqualified; see [compatibility](agent-compatibility.md). A live Claude 250k/300k long-session run remains unverified.

The [2026-10-26 OpenCode experiment](../references/opencode-context-qualification.md) exercised a
real paid DeepSeek V4.1 Flash call with 278,859 input tokens and a native refusal after a tool result
crossed the experimental reserved budget. It establishes a primary HTTP admission mechanism in
an isolated profile; it does not enable Factory strict mode or qualify handover/compaction and
auxiliary-call coverage.

Use `tools/context/run [claude arguments]` for managed interactive/headless runs. It verifies the
current architecture baseline, passes `--autocompact 250000`, and refuses explicit compaction
overrides. Hooks are an accidental-behavior guard, not isolation against malicious code that can
edit its own scripts/settings. Raw CLI launches outside the managed entry point are not qualified.

Verification: `python3 tools/context/tests/test_budget.py`. Synthetic fixtures prove state and
refusal behavior; they do not establish live runtime guarantees. The existing Stop hook remains
a once-only normal sign-off reminder, separate from the mandatory pre-compaction checkpoint.

All three managed entry points are available through `tools/agents/run <agent>`. The original
Claude entry point remains supported and now always enters the repository root before launch.

Checkpoint task-state checks include nonignored untracked files, not only tracked diffs. A resumed
pending warning asks for closure; only a verified actual compaction can report a retained checkpoint.
