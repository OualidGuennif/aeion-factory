# The Codex run

Codex builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[first Claude Code run](../claude_code/archive/run-01/SUMMARY.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` at `578f4f3` (release 1.4.0). It has the base fixes
  from the Claude Code run (FB-002, 004 to 010), Graphify 0.9.97 and Archify v3.2.0 pins, and
  `tools/architecture/ask` with `ask callers`, and the skill `graph`.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git`, holds 163 files and
  no app yet.
- **Fresh state:** `tools/release/release --new-project` reset the copy (FB-003 of run 1, FB-001 of
  Codex): `VERSION` 0.1.0, an empty changelog, and only the "Adapt" task in `work/current.md`.

| Folder | What goes there |
| --- | --- |
| `journal/` | `00-setup.md`, then one file per round, each ending with the record block of `00-start.md` |
| `feedback_for_aeion/` | `FB-001-<slug>.md` …, numbered from 001 for this run, plus an index `README.md` |
| `render/` | round 07: `index.html`, `diagrams/`, `graphify/` |
| `archive/run-NN/` | after round 07: `SUMMARY.md`, `journal/` and `feedback_for_aeion/`; the rest is reset |
| `workspace/` | the factory copy; the app goes in `workspace/app/` |

## Starting Codex
1. Trust the project and enable its hooks (`/hooks`), then restart Codex, as in
   `knowledge/operations/agent-compatibility.md`.
2. Open Codex in `demo/` (or at the repository root; [`../plan/00-start.md`](../plan/00-start.md) says
   why both work). Codex loads the root `AGENTS.md` from the git root down.
3. Paste [`../start/codex/START.md`](../start/codex/START.md) as the first message. Its sandbox writes only below `demo/`, so it asks
   before each `git commit`: approve it.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
| 00 | Setup checks passed; round 01 awaits approval | 743 passed, 2 skipped; hook battery 10 passed, 5 informational; factory checks PASS | 0 during work; 5 expected battery denials | 0 during setup; commit approval requested separately | none new |

Round 00: [journal and retained output](journal/00-setup.md).

| 01 | Scaffold Fresh and Hono | 3 passed | 0 failed; smoke and factory checks PASS | 1 (FB-001) | existing authorization | FB-001 |

| 02 | Ideas API and KV persistence | 28 passed | 0 failed; smoke and factory checks PASS | 0 | existing authorization | none new |

| 03 | SSR page and progressive form | 33 passed | 0 failed; smoke and factory checks PASS | 0 | existing authorization | none new |
