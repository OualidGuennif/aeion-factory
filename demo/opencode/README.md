# The OpenCode run

OpenCode builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
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

## Starting OpenCode
1. OpenCode 2.1.4+ with a provider already connected in its own settings. It loads the root
   `opencode.json` and `.opencode/plugins/factory/` (the hooks), and the nearest `AGENTS.md` above
   `demo/`, which is the root one: `demo/` has none of its own on purpose.
2. Open OpenCode in `demo/` (or at the repository root; [`../plan/00-start.md`](../plan/00-start.md)
   says why both work).
3. Paste [`../start/opencode/START.md`](../start/opencode/START.md) as the first message.

## Results by round

Run: 2026-10-28, one OpenCode session, all rounds pre-authorized by the owner. Factory 1.4.0
(`578f4f3`), Deno 2.9.8, Docker 29.9.2. 51 tests at the end; no container/tests left running.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
| 00 setup | done | 736 factory cases, hook battery 0 failures | 1 (correct: `.env` read refused) | 1 (authorize all rounds) | none |
| 01 scaffold | done | 3 + build + HTTP/dev smoke | 2 (correct: heredoc/pidfile intake) | 0 | none |
| 02 ideas API | done | 24 + smoke | 0 | 0 | none |
| 03 page | done | 31 + smoke | 0 | 0 | none |
| 04 votes | done | 42 + 25/25 concurrent votes + smoke | 1 (correct: heredoc intake again) | 0 | none |
| 05 filters/search | done | 51 + smoke | 0 | 1 (mid-round compact request; checkpoint verified) | none |
| 06 Docker | done | 51 + 5 container checks (healthy, uid 1993, data survives restart, frozen lock) | 0 | 0 | none |
| 07 architecture | done | 14 diagrams validate/render/browser-check; 5 graph answers | 1 (correct: `cat` dump after cd) | 0 | FB-001 |

Findings worth keeping from this run:

- Fresh 2 has no `ALL` handler key: a plain function is the catch-all (`app/routes/api/[...path].ts`).
- `Deno.openKv` needs `"unstable": ["kv"]` **and** `deno.unstable` in the compiler `lib` when `lib` is
  set explicitly, and it does not create the data folder (one module does: `app/store/kv.ts`).
- Same-millisecond ULIDs are random: `monotonicUlid()` keeps KV key order = creation order.
- Bounded optimistic retries cannot land 25 truly-concurrent votes (10 retries → 10 winners): a
  per-id vote chain removes self-contention while the atomic check still guards other writers.
- FB-001: `ask`'s incremental rebuild missed a frontmatter-only spec edit; deleting `.aeion/graph`
  gave the correct answer (`ask` reported a spec gap that was already fixed).

