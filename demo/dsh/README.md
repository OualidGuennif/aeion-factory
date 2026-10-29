# The dsh run

dsh (DeepSeek Harness) builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[first Claude Code run](../claude_code/archive/run-01/SUMMARY.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` at `6e98daa` (release 1.5.0). It has
  the dsh plugin, the one 250k/300k context rule for every harness, and everything the Pi copy has.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git` and no app yet.
- **Fresh state:** `tools/release/release --new-project` reset the copy: `VERSION` 0.1.0, an empty
  changelog, and only the "Adapt" task in `work/current.md`.

| Folder | What goes there |
| --- | --- |
| `journal/` | `00-setup.md`, then one file per round, each ending with the record block of `00-start.md` |
| `feedback_for_aeion/` | `FB-001-<slug>.md` …, numbered from 001 for this run, plus an index `README.md` |
| `render/` | round 07: `index.html`, `diagrams/`, `graphify/` |
| `archive/run-NN/` | after round 07: `SUMMARY.md`, `journal/` and `feedback_for_aeion/`; the rest is reset |
| `workspace/` | the factory copy; the app goes in `workspace/app/` |

## Starting dsh
1. dsh 0.2.1+ with a provider already connected in its own settings. It reads the root `AGENTS.md` and
   `.agents/skills` from any folder below the root, but loads the factory plugin only through a patch
   overlay, so from `demo/` the patch is passed explicitly:
   ```bash
   cd demo && dsh --profile tui --patch ../.dsh/factory.patch.yml
   ```
   The plugin finds `tools/agents/hook.py` by walking up from `demo/`. Started at the repository root,
   `tools/agents/run dsh` adds the same patch.
2. Paste [`../start/dsh/START.md`](../start/dsh/START.md) as the first message.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
