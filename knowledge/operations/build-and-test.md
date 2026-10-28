---
type: Runbook
title: "Build and test"
description: "Every gate of this repository, where to run it, and the language servers."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: ci
    resource: ../../.github/workflows/ci.yml
    title: "CI"
  - id: lsp
    resource: ../../tools/claude-plugins/native-lsp/.lsp.json
    title: "Language-server registrations"
---

# Build and test

CI action revisions are pinned to upstream commit SHAs; review upstream changes before updating them.

The standalone efficiency bundle includes the CRAFTED principles as well as the seven chapters.
Rebuild it with `tools/efficiency/bundle` after editing those sources or `CREDITS.md`; CI rebuilds
it and fails when the committed bundle differs.

| Layer | Gate | From |
| --- | --- | --- |
| Knowledge | `tools/knowledge/knowledge-check` | the root |
| Docs and code links | `tools/knowledge/doc-links` (`--diff origin/main` on a branch) | the root |
| Comments, file size, caps | `tools/repo-health/repo-health` | the root |
| Hooks and tools | `python3 .claude/hooks/test_hooks.py`, `python3 tools/knowledge/tests/test_doc_links.py` | the root |
| Health, push gate and release regressions | `python3 tools/repo-health/tests/test_repo_health.py`, `python3 tools/git-hooks/tests/test_pre_push.py`, `python3 tools/release/tests/test_release.py` | the root |
| Context and analysis regressions | `python3 tools/context/tests/test_budget.py`, `python3 tools/architecture/tests/test_refresh.py` | the root |
| Agent adapters and loop boundaries | `python3 tools/agents/tests/test_hooks.py`, `node --test tools/agents/tests/test_opencode.mjs`, `python3 tools/loops/tests/test_loops.py` | root; Node 18+ |
| Efficiency bundle | `tools/efficiency/bundle`, then `git diff --exit-code efficiency/efficiency-bundle.md` | the root |
| Source analysis (CI on every main update; local run recommended) | `tools/architecture/refresh --target HEAD --base origin/main` after committing | pinned tools installed on the user's yes, Node and Chrome required |
| Your code | add your build, lint and test commands here, copied from CI | |

The pre-commit (`git config core.hooksPath tools/git-hooks`) runs the first three, and the pre-push
refuses a push of `develop` without a recorded `Review: OK` and any direct push to `main`; CI runs
all of them and the security scans, for `main` only.

Many people run Æion Factory in a plain folder, without git. The link and health checks, the context
fingerprint and the session-start summary then walk the files on disk (skipping `.git`, `.aeion`,
dependencies and caches; `.claude/hooks/project_files.py`), and every harness hook command falls back
from `git rev-parse --show-toplevel` to the current folder. Only `doc-links --diff`, which compares
commits, needs git. A folder whose `.git` git cannot read is a broken repository and fails, as does a
missing comparison base; a valid empty change set remains successful and an unavailable check is
never reported as clean.

Header traceability is extension-independent and bounded; see the discovery scope in
[specs-first](../policies/specs-first.md). The Stop reminder preserves spaces/Unicode in edited
paths and reports an unavailable link check once; unreadable input or a session id shaped like a
path has nothing recorded and passes. The path guard and after-edit also cover MultiEdit and
NotebookEdit (`notebook_path`). `repo-health --json` exposes its source suffix
set and selected file count; its caps are not language-aware lint or security coverage.

Policy hooks require Claude Code 2.1.295+ for `onFailure: block`; the Bash/path guard command timeout is three
seconds (context hooks use five; native adapter hooks use fifteen). Independently, the after-edit hook limits each checker to two seconds for fast feedback.
Nonzero exits, missing executables and timeouts produce exit 2 and at most 15 lines
of diagnostics. Direct script tests do not qualify live harness dispatch or runtime isolation.
After-edit checks require macOS, Linux or WSL: a timed-out check's process group is terminated
before capture pipes are drained, so ordinary descendants do not keep working after the timeout.

The same hook suite tests [bounded intake](../policies/bounded-intake.md), including file/range
thresholds, misleading limiters and preserved native edit/range fields. SessionStart adds two
short intake instructions and the flow mode within its existing 25-line cap.

The flow mode is a per-clone Git setting, read from the repository's local config only
(`git config --local`; includes and the global config do not count). The default team flow ends
a task in a pull request with review and green CI. `git config aeion.mode local` sets local play
in the repository's local config: commits go to
`main` directly, the Stop sign-off reminder is silent, and the safety guards (secrets, Git hook
and force-push bypasses, large dumps) stay on. `git config --unset aeion.mode` restores the team flow.

## Language servers

`tools/claude-plugins/` is a local marketplace with `native-lsp`: TypeScript 7 (`tsc --lsp
--stdio`, the project's own compiler), Deno (`deno lsp`) and Java (Eclipse JDT LS on the project's
JDK, data outside the repository). One server per file extension: enable only those you use.

```bash
claude plugin marketplace add ./tools/claude-plugins --scope project
claude plugin install native-lsp@aeion-local --scope project
```

Check: an `initialize` answer, a definition and references through the `LSP` tool, a deliberate
type error reported then cleared, and the same after a fresh session. Roll back with
`claude plugin uninstall native-lsp@aeion-local --scope project`.

Agent-specific setup and qualification: [compatibility](agent-compatibility.md). Integration pins
require Python 3.12+ excluding 3.14.1. `knowledge-check` also validates public root/setup docs and
the portable efficiency bundle; its bundled Superpowers notice is self-contained.
