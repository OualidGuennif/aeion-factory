# Changelog

Every notable change, newest first ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[SemVer](https://semver.org/)). Each change adds its line under Unreleased; `tools/release/release`
dates them at release time. Spec: knowledge/policies/engineering.md

## [Unreleased]

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
