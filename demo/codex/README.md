# The Codex run

Codex builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[Claude Code run](../claude_code/README.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` at `f7bcdab`. It has the base fixes
  from the Claude Code run (FB-002, 004 to 010), Graphify 0.9.97 and Archify v3.2.0 pins, and
  `tools/architecture/ask` with the skill `graph`.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git`, holds 160 files and
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
1. Trust the project and enable its hooks (`/hooks`), then restart Codex, as in
   `knowledge/operations/agent-compatibility.md`.
2. Open Codex in `demo/` (or at the repository root; [`../plan/00-start.md`](../plan/00-start.md) says
   why both work). Codex loads the root `AGENTS.md` from the git root down.
3. Paste [`START.md`](START.md) as the first message. Its sandbox writes only below `demo/`, so it asks
   before each `git commit`: approve it.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
