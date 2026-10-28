# The Codex run

Codex builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[Claude Code run](../claude_code/README.md), so the two can be compared round by round.

- **Factory copy:** `workspace/` (not tracked). It was made from `develop` at `bab0e11`, so it already
  has the eight base fixes from the Claude Code run (FB-002, 004 to 010).
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git`, holds 154 files and
  no app yet.
- **Inherited state:** the copy's `work/current.md` and `CHANGELOG.md` still hold the factory's own
  entries, as they did for the Claude Code run (FB-003).

| Folder | What goes there |
| --- | --- |
| `journal/` | `00-setup.md`, then one file per round, each ending with the record block of `00-start.md` |
| `feedback_for_aeion/` | `FB-001-<slug>.md` …, numbered from 001 for this run, plus an index `README.md` |
| `render/` | round 07: `index.html`, `diagrams/`, `graphify/` |
| `result/` | after round 07: a snapshot of the app and its specs, as in `../claude_code/result/` |
| `workspace/` | the factory copy; the app goes in `workspace/app/` |

## Starting Codex
1. Open Codex at the repository root `aeion-factory/`, not inside `workspace/`. `00-start.md` says why.
2. Trust the project and enable its hooks (`/hooks`), as in
   `knowledge/operations/agent-compatibility.md`.
3. Give it this first message:

   > You are the harness `codex` of the demo in `demo/`. Read `demo/README.md` and `demo/plan/00-start.md`.
   > Work only in `demo/codex/`: the factory copy is `demo/codex/workspace/` (no git), and records go
   > beside it. Do round 00 now, then stop and wait for my yes before each next round. Commit each
   > round on `develop` as `demo(codex): round NN …`; never push.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
