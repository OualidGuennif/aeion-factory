# The Claude Code run 2

Claude Code builds the same Idea Board again from [`../plan/`](../plan/00-start.md) as the
[first Claude Code run](archive/run-01/SUMMARY.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` at `578f4f3` (release 1.4.0). It has the base fixes
  from the Claude Code run (FB-002, 004 to 010), Graphify 0.9.97 and Archify v3.2.0 pins, and
  `tools/architecture/ask` with `ask callers`, and the skill `graph`. The point of this run is to
  check that every fix from run 1 holds.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git`, holds 163 files and
  no app yet.
- **Inherited state:** the copy's `work/current.md` and `CHANGELOG.md` still hold the factory's own
  entries, as they did for the Claude Code run (FB-003).

| Folder | What goes there |
| --- | --- |
| `journal/` | `00-setup.md`, then one file per round, each ending with the record block of `00-start.md` |
| `feedback_for_aeion/` | `FB-001-<slug>.md` …, numbered from 001 for this run, plus an index `README.md` |
| `render/` | round 07: `index.html`, `diagrams/`, `graphify/` |
| `archive/run-NN/` | after round 07: `SUMMARY.md`, `journal/` and `feedback_for_aeion/`; the rest is reset |
| `workspace/` | the factory copy; the app goes in `workspace/app/` |

## Starting Claude Code
1. Open Claude Code at the repository root or in `demo/` ([`../plan/00-start.md`](../plan/00-start.md)
   says why both work). The project hooks in `.claude/settings.json` run from the root either way.
2. Paste [`START.md`](START.md) as the first message.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
