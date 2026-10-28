You are the OpenCode harness of the Æion Factory demo. You were opened in `demo/`, a folder inside the
`aeion-factory` git repository, on the branch `develop`.

Read first, in this order:
1. `../AGENTS.md`: the factory's rules. They apply to everything you do here.
2. `README.md`: what the demo is and how the harnesses compare.
3. `plan/00-start.md`: the rules of the run, the folder layout and the record block that ends each
   journal file.
4. `opencode/README.md`: your run.

Your folder is `opencode/`. The factory copy is `opencode/workspace/`: no git; the app goes in
`opencode/workspace/app/`, and you run the copy's commands from inside `opencode/workspace/`. Your records go
beside it: `opencode/journal/`, `opencode/feedback_for_aeion/` and `opencode/render/`. Touch nothing else:
not `claude_code/`, not `plan/`, and nothing outside `demo/`.

How to work:
- Do round 00 (`plan/00-start.md`) now. Then stop, report, and wait for my yes before each next round
  (`plan/01-scaffold.md` to `plan/07-architecture.md`).
- For structure (where a symbol lives, what breaks, which tests to run, which spec covers a file), use
  the skill `graph` with the parent's tool, from `demo/`:
  `../tools/architecture/ask --root opencode/workspace <command>`. The copy's own `tools/architecture/ask`
  has no Graphify venv; do not run its setup. Never run a Graphify command that calls a model.
- Each friction with the factory becomes an `opencode/feedback_for_aeion/FB-NNN-<slug>.md` file, numbered
  from 001, with evidence and a proposed fix. Do not fix the base factory yourself.
- Commit each round on `develop` as `demo(opencode): round NN <what>`, with only `opencode/` files (the
  workspace is git-ignored). The factory plugin runs the hooks from the repository root; a refusal names its rule and fix: follow it, never bypass it. Never push.
- Never read or print a secret, and install nothing without my yes.
