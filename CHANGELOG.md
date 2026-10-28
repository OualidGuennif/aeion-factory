# Changelog

Every notable change, newest first ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[SemVer](https://semver.org/)). Each change adds its line under Unreleased; `tools/release/release`
dates them at release time. Spec: knowledge/policies/engineering.md

## [Unreleased]

### Added
- `docs/diagrams.html` links every Archify diagram; `tools/architecture/refresh` rebuilds
  `.aeion/analysis/index.html`, a listing of the PASS baselines, newest commit first.
- `demo/`, a playground where an agent builds a real app on a copy of the factory: briefs in
  `demo/plan/`; each `demo/<harness>/` keeps its journal and `feedback_for_aeion/`, and only its `workspace/` is local.

- `tools/factory-tests` runs every factory test suite, as CI now does; `AGENTS.md` names it in one line
  instead of five, so a project has room under the 120-line cap for its own build commands.

### Changed
- Graphify is pinned to the 0.9.97 release and Archify to the v3.2.0 release tag (was 0.9.95 and 13
  commits past v3.2.0); only optional extras changed upstream, so the hashed requirements are unchanged.
- Release source archives leave out `demo/` (`.gitattributes` export-ignore); a release test checks it.

### Fixed
- `doc-links` skips a project nested in this one (its own `AGENTS.md` and `knowledge/`), whose `Spec:`
  pointers name its own knowledge; a demo copy no longer fails the parent's L1 and L3.
- The Bash guard's bounded-intake refusal names its cause (oversized file, variable or glob path, a
  `cat` after a `cd`) instead of always asking for a limiter.
- The Bash guard no longer reads a code property such as Deno KV's `entry.key)` as a key file, in a
  quoted heredoc read by an interpreter or git or written by `cat`/`tee`; unquoted, shell, `xargs`
  and read-loop heredocs stay strict.
- The Graphify graph links each spec to the files its frontmatter `sources` name (`specifies` edges),
  so "which spec covers this file" is answered; unresolved resources are listed in `coverage.json`.
  `graph.py` also accepts a relative root.
- `tools/architecture/refresh` refuses a root that is not its own git repository before any git call,
  instead of analysing the enclosing repository; the doc gives the plain-folder commands.
- Without git, the file walk honours each folder's simple `.gitignore` rules, so build output such as
  Fresh's `app/_fresh/` no longer fails `repo-health` in a plain folder.
- At the 250k alert the checkpoint is admitted from any working directory (relative, absolute or
  `cd <root> &&`), and without `--base` in a plain folder, which could not close before; a refused
  checkpoint names the missing heading or the remaining TODO.

## [1.3.0] - 2026-10-28

### Added
- A `develop` branch for daily work: `tools/git-hooks/pre-push` refuses a push of `develop` without a
  recorded `Review: OK` for the exact commit, and any direct push to `main`.
- Versioning: `VERSION`, this changelog and `tools/release/release`; releases are tagged `vX.Y.Z`.
- Token feedback (advisory): one line, once per turn, when an agent writes prose between tool calls
  or rewrites an existing file of 200+ lines with Write; Claude Code and Codex are covered.
- Plain folders without git: hooks, link and health checks, the context checkpoint and the
  session-start summary work on the files on disk.

### Changed
- Local mode (`git config aeion.mode local`) pushes `main` without the pre-push team gate.
- The context guard finds a workflow agent's transcript under `subagents/workflows/<run>/`, so
  workflow agents (such as a Claude Security scan) are no longer refused every tool call.
- Releases reach `main` through a reviewed `develop → main` pull request merged with a merge commit.
- Main protection allows merge commits and no longer requires linear history, so `develop` stays an
  ancestor of `main`.
- Sign-off and the checkpoint compare against `origin/develop` when it exists.
- CI also runs on pull requests into `develop` (loop pull requests); pushes of `develop` run none.
