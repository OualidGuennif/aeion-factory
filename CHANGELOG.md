# Changelog

Every notable change, newest first ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[SemVer](https://semver.org/)). Each change adds its line under Unreleased; `tools/release/release`
dates them at release time. Spec: knowledge/policies/engineering.md

## [Unreleased]

## [3.0.0] - 2026-11-10

- **Breaking: Graphify and Archify are removed.** The factory now needs only Python 3 and a coding
  agent: no virtual environment, Node or browser install for analysis or diagrams. `tools/architecture/`,
  its CI workflow, the `graph` skill and the Bash guard's Graphify rules are gone; the `axiom` skill and
  `tools/axiom/axiom query` replace `tools/architecture/ask`.
- **AxiomSpec is built in.** The AxiomSpec package (edition 0.3.0) and its two playbooks are vendored in
  `knowledge/axiomspec/`. Each project has one canonical `knowledge/spec/spec.json` (goals, terms,
  requirements, decisions, constraints, scenarios, tests, bindings); `tools/release/release --new-project`
  and `tools/axiom/axiom init` create it.
- `tools/axiom/axiom` (standard library only): strict validation and gates G01-G07 (BCIR constraints
  evaluated on scenarios), a knowledge graph joining spec, docs and code, bounded queries, context
  packets for a change, the generated cockpit `docs/README.md` with SVG diagrams (system, process,
  sequence, use case, state), an eight-section feature export for a build factory, and test evidence
  receipts through a unittest adapter (G09-G11). Unknown is never reported as pass.
- `tools/axiom/axiom check` runs in the pre-commit hook and CI: the spec parses and links, docs cite
  only real IDs, generated docs are current. Docs name the IDs they cover in frontmatter `spec_ids`.
- The factory specifies itself in `knowledge/spec/spec.json`; its architecture diagrams are in the cockpit.
- New demo: the Holiday Planner, a 20-feature AxiomSpec product built in ten rounds, with `demo/check`
  replaying every AxiomSpec step on a fresh copy in seconds. The Idea Board runs stay readable at v2.1.1.
- `template-update` never writes a project's spec, cockpit, views or catalogs; repo-health no longer
  counts a folder releases leave out (`export-ignore`); `factory-tests` reports the JavaScript adapter
  suites as not run when Node is absent.

## [2.1.1] - 2026-11-06

- Fixed: Grok's hook transcript is `updates.jsonl` (older sessions still use `chat_history.jsonl`). The 250k/300k size is `signals.json` `contextTokensUsed`, which falls after compaction. `usage.json` is the billed ledger and only grows, so it does not drive the gate. The shared path guard accepts Grok's `target_file` and `target_directory`.

- Grok runs the shared guards through `.grok/hooks/factory.json`. The Claude budget hook no longer
  latches STOPPED when Grok loads `.claude/settings.json`: a `hookEventName` envelope or an
  `updates.jsonl` or `chat_history.jsonl` transcript is left to the Grok adapter, which reads
  `contextTokensUsed` in `signals.json` for the 250k/300k rule. Compaction cannot be refused, so a compaction before the
  verified handover owes that closure.

## [2.1.0] - 2026-11-06

- The engineering policy and the `build` skill add four principles adapted from ub-mode: the data's
  shape before the logic, a pinned behaviour before a restructuring, a design fitted to the change
  (first principles for new code, the smallest fitting change in a running system), and state that
  survives retries and concurrent writers.
- `template-update` run from a project's own copy says to run it from the factory clone even when
  `--root` names no folder, instead of `no such project`.

## [2.0.3] - 2026-11-04

- Security: the pooled skill-creator eval viewer page escapes quotes and every benchmark value it
  writes, so grader evidence quoting an eval output can no longer add an event handler to the page
  (Claude Security sweep of 2026-11-04, F1).

## [2.0.2] - 2026-11-04

- Fixed: `template-update` also brings forward the factory files a project still holds as an older
  release left them (updates before 2.0.1 moved only the connectors), instead of reporting false
  conflicts or never updating them.
- `template-update` says to run it from the factory clone when started from a project's own copy, and
  its proposal folder ignores itself, so proposals never show up as files to commit.
- Security (Claude Security scans of 2026-11-03): secret file names match in any case and also cover
  `.git-credentials`, `.credentials.json`, `*.env`, `.dev.vars`, `*.ppk`, `*.jks`, `id_*_sk` and
  `terraform.tfstate`; a Grep over a folder outside git checks every file it would read; Claude Code
  settings deny reads of SSH, AWS, GitHub CLI, git and Claude credentials.
- Security: read-only loops refuse `gh` output templates (`--jq`, `--template`) and `--repo`; git
  settings that run a program (`core.fsmonitor`, pagers, editors) are refused through `git config`,
  `-c`, `--config-env` and `GIT_CONFIG_*`.
- Security: loop file tools stay inside the project (`AEION_LOOP`); writing loops get named git
  subcommands, not `git *`; the retro has no `gh api` and writes only hookify rules and skills; the
  inner loop takes only an issue a maintainer wrote; the workflows no longer keep the checkout token.
- Security: an `apply_patch` header padded with spaces or in another case is guarded as the harness
  reads it, and an unknown header is refused; a grep file filter is checked for every harness.
- Fixed: Antigravity 2.0 shell calls carrying `toolSummary` were all refused; its `read_file`,
  `write_file` and `edit_file` tools are now guarded.
- Security: the OpenCode and Pi plugins run only their own checkout's hooks, never a
  `tools/agents/hook.py` found above the session folder. The dsh plugin runs a project's hooks only
  for a project its profile trusts, and refuses tools elsewhere: after installing 2.0.2, run
  `tools/agents/dsh-install --trust <project>` once per project.
- Fixed: `adapter-check` read a `.json` path in a config as a `.js` script, and its repair line could
  name that path instead of the reference.
- Security: two pooled skill scripts are patched (`tools/skills/patches.json`): the skill-creator
  eval viewer answers only its own localhost page and escapes the outputs it embeds, and the
  continuous-learning-v2 instinct import refuses redirects.

## [2.0.1] - 2026-11-03

- `template-update` updates every factory file a release changed, not only the connectors: files you
  left untouched take the release, files you edited are merged, and a conflict keeps your file with a
  proposal under `.aeion/template-update/`. Your instructions, settings, knowledge and changelog stay yours.
- Fixed: a project updated to 2.0.0 kept the old team-default `pre-push` hook.
- `template-update` finds the release your project came from (`.aeion-factory`, else the closest tag),
  so `--from-ref` is optional; it shows the release notes, flags a major version and names migration
  steps such as `git config aeion.mode team`; it refuses to write over uncommitted changes.
- `tools/release/release --new-project` records the factory release in `.aeion-factory`.

## [2.0.0] - 2026-11-03

- Changed: the git lifecycle is off by default. A clone starts in local mode (safety hooks on, no
  develop, review or release gate); `git config aeion.mode team` turns the team flow on.
  **Projects that use the team flow: run `git config aeion.mode team` once in each clone.**
- README reorganized: new project, existing project, optional tools, skills, then every hook.
- In the team flow, session start says when you are on `main` instead of `develop`.

## [1.9.4] - 2026-11-03

- Security: a recursive search that would read a secret file is refused (`grep -r`, `rg -u`, `ack`,
  `ag`, and `rg` outside a git repository); a secret's name is allowed as a search pattern
  (`grep -rn env.local docs`).
- Security: the path guard judges a symlink by its target, so a link to `.env` or `.git/config` is refused.
- `tools/agents/run` and `tools/context/run` name a missing agent binary in one line, not a traceback.
- `tools/agents/pi-rpc` reports a Pi that exits before reading the prompt in one line.
- Session start says when git hooks are off, and how many tasks or changes it left unlisted.
- CI also runs on pushes to `develop`; the Semgrep container is pinned by digest.
- `tools/release/release --new-project` removes the factory's `demo/` from a new project.

## [1.9.3] - 2026-11-02

- Added `tools/agents/run pi rpc`: headless Pi that compacts at 250k and continues in the same process.
- Project updates ship the Pi RPC runner along with the launcher that calls it.

## [1.9.2] - 2026-11-02

- Fixed: headless Pi (`pi -p`) no longer crashes at 250k; it stops cleanly with a verified handover.
- Documented the live 250k runs: dsh and OpenCode compact with a verified handover.

## [1.9.1] - 2026-11-02

- Fixed: a handover verified before a later edit no longer blocks compaction on dsh, Pi and OpenCode.
- dsh: when compaction does not run, the messages say to stop and resume from the handover.
- `template-update` takes the source release as `--from-ref` and never touches your `VERSION`.
- `template-update` and `adapter-check` refuse symlinked connector files and restore launcher permissions.

## [1.9.0] - 2026-11-01

- Fixed the 250k gate staying shut after a second compaction or after a verified handover.
- dsh compacts reliably: handover, compact, keep going.

## [1.8.9] - 2026-11-01

- Fixed: the 250k gate releases once the context falls back under 250k (dsh).

## [1.8.8] - 2026-11-01

- Fixed: a verified handover releases the 250k/300k gate (dsh web).

## [1.8.7] - 2026-11-01

- dsh web compacts through its `/compact` command.

## [1.8.6] - 2026-11-01

- dsh web compacts at the gate instead of waiting for its own pressure compaction.

## [1.8.5] - 2026-11-01

- Fixed: dsh sessions no longer become unopenable after a guard message.
- `adapter-check` flags a connector message sent without a role.

## [1.8.4] - 2026-11-01

- The 250k gate is advisory where the harness cannot compact (dsh web), so it no longer stalls.
- Pi compacts at its model window even before the handover is verified, and owes it after.
- Added `tools/agents/dsh-install`: installs the dsh desktop plugin pinned to a release tag.
- `adapter-check --ref <tag|branch>` checks connectors against any git reference.
- Added `tools/agents/template-update` and its skill: move an adopted project to a new release.
- Headless Pi needs `-e .pi/extensions/factory/index.js`; without it no guard loads.

## [1.8.3] - 2026-11-01

- Added `tools/agents/adapter-check`: catches connector copies that drifted from the factory.
- Added prompt-injection warnings on fetched and tool results (`prompt-defense.py`); they never block.
- dsh, Pi, OpenCode and Codex show that warning.
- The security and engineering policies state the prompt-defense baseline and the three passes.

## [1.8.2] - 2026-10-31

- Fixed: dsh and Pi end the turn on a terminal stop instead of looping.
- Fixed: at 300k a failing check no longer blocks the compaction; the handover stays owed.

## [1.8.1] - 2026-10-31

- Pi: the 250k messages name the checkpoint command, and closure retries stop after three.
- The checkpoint shows why a check failed and suggests a base that exists.

## [1.8.0] - 2026-10-31

- Added `tools/knowledge/stale` and `tools/knowledge/orphans`.
- Added the golden task set: twelve evaluation tasks with a local record and report.
- Added `tools/skills/lint` to check every native skill.
- `AGENTS.md` is now a short procedure: self-check, stop-and-ask, rules.
- Stricter input checks in the knowledge and evaluation tools.

## [1.7.0] - 2026-10-31

- Stronger native skills, plus `skill-route` to pick guidance from an optional pool.
- Added an offline pool of 525 skills and 99 agent profiles, with licenses and integrity checks.

## [1.6.2] - 2026-10-29

- Token feedback also flags JSON progress notes; keep reasoning private and use tools directly.

## [1.6.1] - 2026-10-29

- Simpler README; setup details moved to the getting-started guide.

## [1.6.0] - 2026-10-29

- Droid: compaction before a verified handover runs, and the handover is owed after it.
- dsh: the guards run in its `web` profile; one background server guards every factory project.
- Added `tools/architecture/gallery`: one offline page with every Archify diagram.
- Fixes from the first demo run: fewer false refusals in the bash guard, clearer gate messages,
  and `doc-links` checks that each spec lists the files it covers.
- demo: a dsh run; run 1 archived with a comparison table.

## [1.5.0] - 2026-10-29

- Added DeepSeek Harness (dsh) support: `tools/agents/run dsh`.
- Added `tools/release/release --new-project` to start a project from a copy of the factory.
- One context rule for every harness: 250k handover then compaction, 300k forces both.
- Fixed closure stalls around compaction in OpenCode, Codex and Pi.
- Devin and Droid hooks still guard a payload with no event name or session id.

## [1.4.0] - 2026-10-28

- Added `tools/architecture/ask` and the skill `graph`: exact code answers with no LLM.
- Added `ask callers` through the project's language server.
- Added Pi support (1.4.0+) and `tools/factory-tests`, which runs every suite as CI does.
- Added `demo/`, a playground for building a real app with each harness.
- The bash guard refuses Graphify's LLM and installer commands.
- Graphify and Archify pinned to release tags; release archives leave out `demo/`.
- Fixed false refusals and unclear messages in the bash guard, and the checkpoint from any folder.
- Fixed OpenCode in a subfolder, nested projects in `doc-links`, and `repo-health` without git.

## [1.3.0] - 2026-10-28

- Added the `develop` branch flow: a recorded review before each push, releases by PR to `main`.
- Added versioning: `VERSION`, this changelog and `tools/release/release`.
- Added token feedback (advisory) and support for plain folders without git.
- Local mode pushes `main` without the team gate.
- Workflow agents (such as a Claude Security scan) are no longer refused every tool call.
