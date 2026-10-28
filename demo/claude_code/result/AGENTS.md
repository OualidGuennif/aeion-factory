# Idea Board: the app Claude Code built (snapshot)

This is a read-only snapshot of what Claude Code built in the git-less factory copy during rounds 01–07.
It holds the app source (`app/`) and the three specs written before the code (`knowledge/`).
The working copy, `../workspace/`, is not tracked; this snapshot is what stays in git.

- Taken: 2026-10-28, after round 07.
- Not copied: `node_modules/`, `_fresh/`, `data/`.
- Replay from scratch: `../../plan/00-start.md`.

## Run it

```bash
cd app && deno install && deno task test
cd app && deno task build && deno task start
cd app && docker compose up --build
```

Do not edit this snapshot. A new run starts again from a fresh factory copy.
