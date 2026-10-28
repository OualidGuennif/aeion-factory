# The Codex run

Codex builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[first Claude Code run](../claude_code/archive/run-01/SUMMARY.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` at `578f4f3` (release 1.4.0). It has the base fixes
  from the Claude Code run (FB-002, 004 to 010), Graphify 0.9.97 and Archify v3.2.0 pins, and
  `tools/architecture/ask` with `ask callers`, and the skill `graph`.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git`, holds 163 files and
  no app yet.
- **Inherited state:** this copy was made before `tools/release/release --new-project`; Codex reset its
  `work/current.md` by hand (its FB-001, like FB-003 of run 1).

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
