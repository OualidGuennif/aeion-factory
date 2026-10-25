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
  - resource: ../../.opencode/plugins/factory.js
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
- OpenCode loads root `opencode.json` and `.opencode/plugins/factory.js`. Auto-compaction remains
  native to its selected model; no supported fixed 250k setting is invented.
- Both adapters enforce supported Bash/path refusals, edit feedback and a verified handover
  before compaction. Native token stops and strict pre-request 300k admission are unqualified.
- Raw command/MCP paths, host-managed/cloud orchestration and deliberate local modification are
  outside any complete isolation claim. Native project/hook trust and sandbox controls still apply.
- All managed CLI launchers enter the repository root and require an exact-HEAD architecture baseline.

## Verification

Test real tool payloads, patch paths, denied secrets, checker failures and compaction with and
without a current checkpoint. A missing callback/runtime is unverified, never a pass. Runtime
qualification and setup commands are recorded below.

## Primary interfaces

- https://learn.chatgpt.com/docs/hooks
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/build-skills
- https://opencode.ai/docs/plugins/
- https://opencode.ai/docs/config/
- https://opencode.ai/docs/skills/

## Setup

1. Follow README common checks and the mandatory architecture baseline. Install the chosen native
   CLI separately; preserve user account/provider settings.
2. Claude: trust the workspace, then `tools/agents/run claude`.
3. Codex: trust the project in native settings, review/enable the local hooks in `/hooks`, restart,
   then `tools/agents/run codex`. A trusted project and trusted hook sources are distinct. Do not
   disable trust checks globally to make discovery appear successful.
4. OpenCode: `tools/agents/run opencode`. The root config selects the maintained skill directory;
   the native loader installs the pinned plugin package. A database schema conflict can use
   `--isolated`, a separate ignored XDG profile; connect that profile's provider natively.

The shared guards are basename/command-pattern safeguards. Codex native Bash and apply_patch
payloads are normalized explicitly, including deleted/moved patch paths. OpenCode maps native
camelcase file paths and tool events, appends edit feedback to tool output, and injects the exact
verified handover pointer during compaction. Its idle event logs sign-off feedback and cannot
force the model to continue. Shell edits and arbitrary MCP tools are not complete edit coverage.

## Qualification and limits

Regression commands: `python3 tools/agents/tests/test_hooks.py`,
`node --test tools/agents/tests/test_opencode.mjs` and `python3 tools/loops/tests/test_loops.py`.
These exercise real guard processes, payload normalization, patch paths, failure decisions,
checkpoint invalidation, process deadlines, turn caps and issue severity routing.

On 2026-10-25, native Codex 0.164.0-alpha.11.1 discovered all 15 shared skills. Its native
config diagnostic correctly reported this new project layer as untrusted; no persisted user trust
was changed. Users must complete the native trust setup above. Synthetic direct adapter calls do
not prove project-local dispatch while that layer is disabled.

OpenCode 1.19.4 discovered all 15 skills with a fresh isolated profile. Its binary archive SHA-256
was verified against the official release digest. A normal-profile probe hit an existing database
schema conflict; it was preserved. The diagnostic's large stdout needed file capture to avoid
truncation; a partial skill list was not accepted as a successful discovery.

Real model-driven qualification is separate: it must show actual file changes and a witnessed
native guard denial in a disposable repository, not merely an agent's completion statement.
No native long-context 250k/300k run or absolute admission ceiling is claimed. Local hook failures
can be advisory in some native events; retain native sandbox/permissions and check actual dispatch.
Hosted/cloud orchestration and optional scheduled native actions require separate qualification.
