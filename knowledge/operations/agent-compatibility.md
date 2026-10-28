---
type: Runbook
title: "Claude Code, Codex, OpenCode, Devin, Droid and Antigravity"
description: "One Æion Factory instruction/skill source, runtime-specific adapters, setup and explicitly bounded guarantees."
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
  - resource: ../../.devin/config.json
    title: "Devin import settings"
  - resource: ../../.devin/hooks.v1.json
    title: "Devin hook registrations"
  - resource: ../../.factory/settings.json
    title: "Droid hook registrations"
  - resource: ../../.agents/hooks.json
    title: "Antigravity hook registrations"
generated:
  by: aeion-factory/1.2
  at: 2026-10-25
---

# Agent compatibility

AGENTS.md, Knowledge, task state, checker commands and the reviewed PR workflow are shared.
Claude Code remains the original integration. Codex, OpenCode, Devin, Droid and Antigravity use their
documented native configuration and small adapters to the existing guards/checkpoints; copying a
directory does not establish loaded hooks or identical runtime guarantees.

## Contract

- Keep existing `.claude/skills` as the maintained skill source. Codex discovers symlinked folders
  under `.agents/skills`; OpenCode already discovers the Claude-compatible paths.
- Codex local trusted projects enable `.codex/config.toml` and `.codex/hooks.json`. Its native
  auto-compaction threshold is 250000. Its hook transcript format is not a stable token API.
- OpenCode 2.1.4+ loads root `opencode.json` and `.opencode/plugins/factory/index.js`. Auto-compaction remains
  native to its selected model; no supported fixed 250k setting is invented.
- Both adapters enforce supported Bash/path refusals, edit feedback and a verified handover
  before compaction; the first refused compaction creates the skeleton to fill. Native token stops and strict pre-request 300k admission are unqualified.
- Devin CLI reads `AGENTS.md` and `.agents/skills` natively. By default it also imports
  `.claude/settings.json` hooks, but its tools are named `exec`, `read`, `edit`, `write` and
  `apply_patch`, so Claude matchers never fire and the matcher-less Claude budget hook reads a
  transcript Devin does not write. `.devin/config.json` therefore turns the Claude import off, and
  `.devin/hooks.v1.json` sends SessionStart, PreToolUse, PostToolUse and Stop (no matchers) to
  `tools/agents/hook.py devin`. The adapter maps the tool names (also `bash`, `shell`, `grep`, in
  any case) to the shared guards; an unknown tool carrying a `command` string goes through the
  shell guard, and through the path guard too if it names a file. A refused tool call gets
  Devin's `{"decision": "block", "reason": ...}`; a failed Stop or SessionStart gets
  `continue: false`, because Devin's block on Stop means "keep going".
  A payload without `session_id` uses one key per clone, so sign-off reminders are shared across
  that clone's Devin sessions. Devin has no Æion Factory compaction checkpoint or token stop.
- Droid, the CLI of Factory (factory.ai, a product separate from Æion Factory), reads `AGENTS.md`,
  `.agents/skills` and `.factory/settings.json`. That is why Æion Factory's local state lives in
  `.aeion/` and only Droid's config is tracked in `.factory/`. Its hooks send SessionStart,
  PreToolUse, PostToolUse and Stop to `tools/agents/hook.py droid`. Droid payloads and decisions
  are Claude-shaped; the adapter maps `Execute`, `Create` and `ApplyPatch` (patch text in
  `command`, `patchText`, `patch` or `input`) to the shared guards; a tool outside the known
  names carrying a `command` string goes through the shell guard (and the path guard for a
  file). It refuses with `permissionDecision: deny`. Droid has no Æion Factory compaction
  checkpoint or token stop.
- Google Antigravity (the `agy` CLI and the IDE) reads `AGENTS.md` and `.agents/skills`, and
  workspace hooks from `.agents/hooks.json` once the folder is trusted. One `aeion-factory` group
  sends PreToolUse and PostToolUse (matcher `.*`) and Stop to `tools/agents/hook.py antigravity
  <event>`: the payload names no hook event or session, so the event is an argument and the
  session key is per clone, as for Devin. The adapter reads `toolCall {name, args}`, maps
  `run_command` (`CommandLine`) to Bash, `view_file` to Read, `write_to_file` to Write and
  `replace_file_content`/`multi_replace_file_content` to Edit and `grep_search` to Grep. For any
  tool, including MCP tools, every nonempty string at any depth under an argument whose name,
  ignoring case and `_`/`-`, ends in path, file, dir, directory or uri, or their plurals
  (`AbsolutePath`, `TargetDirectories`, `file_path`, `Uri`; a `file:` URI is decoded to its path),
  goes through the path guard; `view_code_item`'s `NodePaths` are code symbols and are skipped. A
  mapped file tool with none is refused. Not recognized: other names (`target`, `Url`), text typed
  into a running command (`send_command_input`) and Windows paths. `view_file`'s
  `StartLine`/`EndLine` become the intake window; `grep_search` with `MatchPerLine: false` lists
  names only. For any tool, every string at any depth under an argument whose name ends in
  include, glob or pattern, or their plurals (`Includes`, `IncludePattern`, `file_pattern`), goes
  through the Grep glob check, so a filter that names a secret is refused, and so is a
  non-string one. Any tool with a `CommandLine` goes through the
  shell guard, as does a `command` or `commandLine` argument in any case; a call with two is
  refused. `Cwd` or `workdir` in any case (a `file:` URI decoded) is the shell's directory; two
  or a non-string one are refused. On a shell call any other argument must be a flag or a
  number, since the guard cannot tell which one a tool runs in; a text, list or object is refused.
  The guards see only fields the adapter derives, never a raw `limit` or output mode from the
  model. A pre-tool payload without `toolCall` is refused. A pre-tool answer is always an
  explicit `{"decision": "allow"}` or `{"decision": "deny", "reason": ...}`, since Antigravity
  reads an empty answer as a refusal. Unverified until a live run: whether that `allow` also
  skips Antigravity's own approval prompt (a `run_command` with `SafeToAutoRun: false`); until
  then, assume it may. No compaction checkpoint or token stop.
- Managed CLI launchers enter the repository root and check the exact-HEAD architecture baseline;
  its absence is a warning, because installing the integrations needs the user's yes.
- Raw command/MCP paths, host-managed/cloud orchestration and deliberate local modification are
  outside any complete isolation claim. Native project/hook trust and sandbox controls still apply.
- The shared launcher also aligns `PWD`: OpenCode 2.1.4 uses it to select the run's location, so
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
- https://docs.devin.ai/cli/extensibility/hooks/overview
- https://docs.devin.ai/cli/reference/configuration/read-config-from
- https://docs.devin.ai/cli/extensibility/skills/overview
- https://docs.factory.ai/reference/hooks-reference
- https://docs.factory.ai/cli/configuration/hooks-guide
- https://docs.factory.ai/cli/configuration/skills
- https://antigravity.google/docs/hooks
- https://antigravity.google/docs/rules
- https://github.com/google-antigravity/antigravity-cli/blob/main/CHANGELOG.md

## Setup

1. Follow the README common checks. Offer the recommended architecture baseline and install it
   only on the user's yes ([architecture maintenance](architecture-maintenance.md)). Install the
   chosen native CLI separately; preserve user account/provider settings.
2. Claude: trust the workspace, then `tools/agents/run claude`.
3. Codex: trust the project in native settings, review/enable the local hooks in `/hooks`, restart,
   then `tools/agents/run codex`. A trusted project and trusted hook sources are distinct. Do not
   disable trust checks globally to make discovery appear successful.
4. OpenCode: `tools/agents/run opencode`. The root config selects the maintained skill directory;
   the native loader loads the local plugin directory. A database schema conflict can use
   `--isolated`, a separate ignored XDG profile; connect that profile's provider natively.
5. Devin CLI: `devin` or `tools/agents/run devin` from the repository root. Approve the project
   hooks if Devin asks. Keep the model/provider choice in Devin's own user settings.
6. Droid: `droid` or `tools/agents/run droid` from the repository root. Approve the project hooks
   if Droid asks; account and model stay in Droid's user settings (`~/.factory/`).
7. Antigravity: `agy` or `tools/agents/run antigravity` from the repository root, or open the
   folder in the IDE. Trust the folder so `.agents/hooks.json` loads; `/hooks` lists it.

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
The [dated OpenCode experiment](../references/opencode-context-qualification.md) covers a native
278k-input call and refusal of an over-budget tool continuation in an isolated primary-HTTP profile.
No full 250k handover/compaction cycle or absolute Æion Factory admission ceiling is claimed. Local hook failures
can be advisory in some native events; retain native sandbox/permissions and check actual dispatch.
Hosted/cloud orchestration and optional scheduled native actions require separate qualification.

Devin is not yet qualified live: no Devin CLI ran in the change that added it. The hook file shape,
tool names, `DEVIN_PROJECT_DIR` and the block decision follow Devin's documentation and two public
integrations verified on Devin 3000.11.3. To qualify, in a disposable clone ask Devin to `cat .env`
and to edit a file: the first must be refused with the guard's reason, the second must name the
covering doc. Devin cloud sessions do not read `.devin/` and are not covered.

Droid is not yet qualified live either. docs.factory.ai was unreachable from the container that
added it, so the payload shape, tool names and `$FACTORY_PROJECT_DIR` follow search excerpts of
its hooks reference and public Droid hook integrations. Unverified: `ApplyPatch`'s input field
(an unknown field is refused, failing closed) and whether Droid also loads `.claude/` hooks.
Qualify it like Devin: `cat .env` refused with the guard's reason, an edit naming its covering doc.

Antigravity is not yet qualified live either; antigravity.google was unreachable from the
container that added it. The `toolCall` payload, `run_command`'s `CommandLine`, the decisions and
`.agents/hooks.json` follow the CLI changelog, a CLI issue quoting a real 1.4.4 payload and
search excerpts of the hooks page. Unverified: the exact case of the file tools' path fields
(an unknown field on a mapped file tool is refused), whether `StartLine` is 1-based, the Stop answer, and whether the IDE runs
workspace hooks (a forum report says its PostToolUse did not fire). A hook that crashes or
times out blocks the call. Qualify it with `agy`: `cat .env` and a view of that file refused
with the guard's reason, and an edit naming its covering doc; then repeat in the IDE.

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
