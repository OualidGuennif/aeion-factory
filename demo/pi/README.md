# The Pi run

Pi builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[Claude Code run](../claude_code/README.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` after the Pi adapter landed. It has
  the base fixes from the Claude Code run (FB-002, 004 to 010), Graphify 0.9.97 and Archify v3.2.0 pins,
  `tools/architecture/ask` with `ask callers`, and the skill `graph`.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git` and no app yet.
- **Inherited state:** the copy's `work/current.md` and `CHANGELOG.md` still hold the factory's own
  entries, as they did for the Claude Code run (FB-003).

| Folder | What goes there |
| --- | --- |
| `journal/` | `00-setup.md`, then one file per round, each ending with the record block of `00-start.md` |
| `feedback_for_aeion/` | `FB-001-<slug>.md` …, numbered from 001 for this run, plus an index `README.md` |
| `render/` | round 07: `index.html`, `diagrams/`, `graphify/` |
| `result/` | after round 07: a snapshot of the app and its specs, as in `../claude_code/result/` |
| `workspace/` | the factory copy; the app goes in `workspace/app/` |

## Starting Pi
1. Pi 1.4.0+ with a provider already connected in its own settings. It reads the root `AGENTS.md` and
   `.agents/skills` from any folder below the root, but loads `.pi/extensions/` only from the folder it
   starts in, so from `demo/` the extension (the hooks) is passed explicitly:
   ```bash
   cd demo && pi -e ../.pi/extensions/factory/index.js
   ```
   The extension finds `tools/agents/hook.py` by walking up from `demo/`. Started at the repository
   root, `tools/agents/run pi` loads it on its own once the project is trusted.
2. Paste [`START.md`](START.md) as the first message.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
