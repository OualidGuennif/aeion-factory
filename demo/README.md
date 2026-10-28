# Demo: Æion Factory on a real app, one agent harness at a time

An agent builds the same small app, **Idea Board**, inside a copy of Æion Factory that has no git. The
stack is Deno 2, Fresh 2 with Vite, Hono under `/api`, Deno KV, and Docker. The agent follows the
briefs in [`plan/`](plan/00-start.md), one round per file, and journals what really happened.

Each friction with the factory becomes a feedback file. The small ones are fixed in the base factory
on `develop`, each with a test, so the next harness starts from a better factory.

## Replay it with another harness

1. Create the copy from the repository root, replacing `<harness>` with the harness name:

   ```bash
   mkdir -p demo/<harness>/workspace && git archive HEAD -- . ':(exclude)demo' | tar -x -C demo/<harness>/workspace && tools/release/release --new-project --root demo/<harness>/workspace
   ```

2. Create `journal/`, `feedback_for_aeion/` and `render/` beside it. The layout is in
   [`plan/00-start.md`](plan/00-start.md).
3. Open the agent at the repository root or in `demo/` ([why both work](plan/00-start.md)). Give it the
   harness's `START.md` as its first message from [`start/`](start/README.md), which also says how to set up each harness's skills and hooks, then one round
   at a time.
4. Every round's journal ends with the same record block, so the runs can be compared.

## Results by harness

| Harness | Factory | Rounds done | Final tests | Feedback (fixed) | Human help | Run |
| --- | --- | --- | --- | --- | --- | --- |
| Claude Code, run 1 | 1.3.0 `fb2af90` | 8 of 8 | 72 + 5 container checks | 10 (8) | approvals, 3 checkpoints | [archive/run-01/](claude_code/archive/run-01/SUMMARY.md) |
| Claude Code, run 2 | 1.4.0 `578f4f3`, every fix above | not started | | | | [claude_code/](claude_code/README.md) |
| Codex | 1.4.0 `578f4f3`, every fix above | not started | | | | [codex/](codex/README.md) |
| OpenCode | 1.4.0 `578f4f3`, every fix above | not started | | | | [opencode/](opencode/README.md) |
| Pi | 1.4.0 `578f4f3`, every fix above | not started | | | | [pi/](pi/README.md) |

Shared tools: [`batteries/hooks_battery.py`](batteries/hooks_battery.py) feeds real payloads to a
copy's Claude hooks.
