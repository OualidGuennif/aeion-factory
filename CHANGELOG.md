# Changelog

Every notable change, newest first ([Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
[SemVer](https://semver.org/)). Each change adds its line under Unreleased; `tools/release/release`
dates them at release time. Spec: knowledge/policies/engineering.md

## [Unreleased]

### Added
- A `develop` branch for daily work: `tools/git-hooks/pre-push` refuses a push of `develop` without a
  recorded `Review: OK` for the exact commit, and any direct push to `main`.
- Versioning: `VERSION`, this changelog and `tools/release/release`; releases are tagged `vX.Y.Z`.
- Plain folders without git: hooks, link and health checks, the context checkpoint and the
  session-start summary work on the files on disk.

### Changed
- Releases reach `main` through a reviewed `develop → main` pull request merged with a merge commit.
- Sign-off and the checkpoint compare against `origin/develop` when it exists.
