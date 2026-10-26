---
type: Runbook
title: "Claude Code, Codex and OpenCode"
description: "One Factory instruction/skill source, runtime-specific adapters, setup and explicitly bounded guarantees."
status: stable
sources:
  - resource: ../../tools/agents/hook.py
    title: "Native payload adapter"
  - resource: ../../tools/agents/run
    title: "Managed agent launch"
  - resource: ../../.codex/config.toml
    title: "Codex native compaction config"
  - resource: ../../.codex/hooks.json
    title: "Codex hook registrations"
  - resource: ../../opencode.json
    title: "OpenCode native config"
  - resource: ../../.opencode/plugins/factory/index.js
    title: "OpenCode plugin callbacks"
generated:
  by: aeion-factory/1.2
  at: 2026-10-25
---

# Agent compatibility

AGENTS.md, Knowledge, task state, checker commands and the reviewed PR workflow are shared.
Claude Code remains the original integration. Codex and OpenCode use their documented native
configuration and small adapters to the existing guards/checkpoints; copying a directory does
not establish loaded hooks or identical runtime guarantees.

## Contract

- Keep existing `.claude/skills` as the maintained skill source. Codex discovers symlinked folders
  under `.agents/skills`; OpenCode already discovers the Claude-compatible paths.
- Codex local trusted projects enable `.codex/config.toml` and `.codex/hooks.json`. Its native
  auto-compaction threshold is 250000. Its hook transcript format is not a stable token API.
- OpenCode 2.1.4+ loads root `opencode.json` and `.opencode/plugins/factory/index.js`. Auto-compaction remains
  native to its selected model; no supported fixed 250k setting is invented.
- Both adapters enforce supported Bash/path refusals, edit feedback and a verified handover
  before compaction. Native token stops and strict pre-request 300k admission are unqualified.
- Raw command/MCP paths, host-managed/cloud orchestration and deliberate local modification are
  outside any complete isolation claim. Native project/hook trust and sandbox controls still apply.
- All managed CLI launchers enter the repository root and require an exact-HEAD architecture baseline.
  The shared launcher also aligns `PWD`: OpenCode 2.1.4 uses it to select the run's location, so
  changing only the process working directory can load another project's plugin/configuration.

## Verification

Test real tool payloads, patch paths, denied secrets, checker failures and compaction with and
without a current checkpoint. A missing callback/runtime is unverified, never a pass. Runtime
qualification and setup commands are recorded below.

## Primary interfaces

- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/build-skills
- https://opencode.ai/v2/docs/build/plugins/
- https://opencode.ai/v2/docs/config/
- https://opencode.ai/v2/docs/skills/

## Setup

1. Follow README common checks and the mandatory architecture baseline. Install the chosen native
   CLI separately; preserve user account/provider settings.
2. Claude: trust the workspace, then `tools/agents/run claude`.
3. Codex: trust the project in native settings, review/enable the local hooks in `/hooks`, restart,
   then `tools/agents/run codex`. A trusted project and trusted hook sources are distinct. Do not
   disable trust checks globally to make discovery appear successful.
4. OpenCode: `tools/agents/run opencode`. The root config selects the maintained skill directory;
   the native loader loads the local plugin directory. A database schema conflict can use
   `--isolated`, a separate ignored XDG profile; connect that profile's provider natively.

The shared guards are basename/command-pattern safeguards. Codex native Bash and apply_patch
payloads are normalized explicitly, including deleted/moved patch paths. OpenCode maps native
camelcase file paths and tool events, appends edit feedback to tool output, and injects the exact
verified handover pointer during compaction. Use the shared sign-off skill before finishing;
the plugin does not claim an idle hook forces continuation. Shell edits and arbitrary MCP tools are not complete edit coverage.

The adapter preserves Read/Grep range/result limits and the real edit kind when invoking shared
[intake guards](../policies/bounded-intake.md). OpenCode V2 uses `path`, 1-based `offset` and
`limit`; Grep's native `limit` is accepted alongside Claude's `head_limit`. Patch path checks use
Edit semantics, so checking a patch never becomes an accidental full-file Read refusal.

## Qualification and limits

Regression commands: `python3 tools/agents/tests/test_hooks.py`,
`node --test tools/agents/tests/test_opencode.mjs` and `python3 tools/loops/tests/test_loops.py`.
These exercise real guard processes, payload normalization, patch paths, failure decisions,
checkpoint invalidation, process deadlines, turn caps and issue severity routing.

Native qualification uses both discovery and witnessed tool dispatch. Codex needs a trusted project
and enabled hook sources; an untrusted layer being ignored is expected. OpenCode requires 2.1.4+
V2 domain callbacks: legacy function exports can appear in discovery without executing.

Real model-driven qualification is separate: it must show actual file changes and a witnessed
native guard denial in a disposable repository, not merely an agent's completion statement.
No native long-context 250k/300k run or absolute admission ceiling is claimed. Local hook failures
can be advisory in some native events; retain native sandbox/permissions and check actual dispatch.
Hosted/cloud orchestration and optional scheduled native actions require separate qualification.

OpenCode 2.1.4 is the qualified V2 target. Legacy 1.19.4 can discover skills but does not dispatch
these V2 callbacks; do not claim its guards are working from discovery alone. The plugin is a
directory with a default id/setup entrypoint and uses no SDK dependency.

OpenCode consumes a verified receipt before each compaction attempt. A retry must verify a new
checkpoint; it never silently reuses a receipt from an earlier compaction. The plugin imports only
Node built-ins and does not bundle an unused SDK or its dependency graph.

Malformed, non-object or oversized native input exits 2 without echoing the payload. A generic
stop JSON object with exit 0 is insufficient for a Codex PreToolUse decode failure.

On 2026-10-26, real disposable model tasks passed with native Codex and OpenCode 2.1.4 using
paid `opencode-go/deepseek-v4.1-flash`: source, owning doc and task state changed, guard refusals
were witnessed, and independent documentation/diff checks passed. OpenCode's denied call had
no completed-tool event. This qualifies bounded tool dispatch, not long-context admission.
Run disposable repositories outside a configured ancestor project: OpenCode inherits parent
configuration and can select that ancestor's plugin instead of the instrumented local copy.
