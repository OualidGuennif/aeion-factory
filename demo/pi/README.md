# The Pi run

Pi builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
[first Claude Code run](../claude_code/archive/run-01/SUMMARY.md), so the runs can be compared round by round.

- **Factory copy:** `workspace/` (not tracked), made from `develop` at `6e98daa` (release 1.5.0). It has
  the one 250k/300k context rule, Pi's resume after compaction, the base fixes from the Claude Code run (FB-002, 004 to 010), Graphify 0.9.97 and Archify v3.2.0 pins,
  `tools/architecture/ask` with `ask callers`, and the skill `graph`.
- **Command:** `git archive HEAD -- . ':(exclude)demo'`. The copy has no `.git` and no app yet.
- **Fresh state:** `tools/release/release --new-project` reset the copy (FB-003 of run 1, FB-001 of
  Codex): `VERSION` 0.1.0, an empty changelog, and only the "Adapt" task in `work/current.md`.

| Folder | What goes there |
| --- | --- |
| `journal/` | `00-setup.md`, then one file per round, each ending with the record block of `00-start.md` |
| `feedback_for_aeion/` | `FB-001-<slug>.md` …, numbered from 001 for this run, plus an index `README.md` |
| `render/` | round 07: `index.html`, `diagrams/`, `graphify/` |
| `archive/run-NN/` | after round 07: `SUMMARY.md`, `journal/` and `feedback_for_aeion/`; the rest is reset |
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
2. Paste [`../start/pi/START.md`](../start/pi/START.md) as the first message.

## Results by round
To fill in as the rounds are done.

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
| 00 setup | factory-tests and the hooks battery pass; no `Stop` hook, so `sign-off.py` never fires in a Pi session | factory-tests PASS; battery 15/15 | 1 | 1 (the owner switched the model) | none |
| 01 scaffold | Fresh 2 + Vite titled Idea Board, Hono under `/api`, `GET /api/health`, `PORT` wrapper | 6 | 2 | 0 | FB-001 |
| 02 ideas API | create, list, read on Deno KV; pure validation; monotonic ULIDs | 38 | 0 | 0 | none |
| 03 ideas page | SSR page with a no-JavaScript form and one island; refusals keep what was typed | 50 | 1 | 0 | none |
| 04 votes | atomic vote + vote index, `sort=recent\|votes`, 25 concurrent votes all count | 66 | 0 | 0 | none |
| 05 tags and search | tag index, `tag=` + `q=` combining, clear link, tag chips | 79 | 0 | 0 | none |
| 06 Docker | pinned image, `deno` user, named volume, self-answered health check | 79 + 5 container checks | 0 | 0 | none |
| 07 architecture | 14 validated Archify diagrams, an offline gallery, five `ask` questions; the graph found a spec/source gap | 79 + 14/14 diagram gates | 1 | 0 | FB-002 |

## Viewing the gallery
`render/index.html` opens offline, but browsers refuse some `file://` paths (macOS protects the
Desktop) and block local iframes, so a direct double-click can show "Access to the file was
denied". Serve the folder instead, in a terminal you leave open:

```bash
cd demo/pi/render && python3 -m http.server 8137 --bind ::
```

Then open <http://127.0.0.1:8137/>. `--bind ::` listens on IPv6 and IPv4, so `localhost` works
too; without it Python listens on IPv4 only, which is what makes Firefox report a failed
connection on `localhost:8137`. The diagrams themselves (`render/diagrams/*.html`) are
self-contained, with no network request; served the same way they render everywhere.

## What this run showed
- **The context rule works end to end.** The 250k alert fired in round 07, refused every tool call
except closure, and the session wrote its handover, updated `work/current.md`, passed
`checkpoint --verify`, compacted and resumed the same round without losing a step. The one friction
(handover headings that nothing documents) is FB-002.
- **The one real gap against the Claude Code run.** Pi has no `Stop` event, so `sign-off.py` never
runs. Nothing else differed: the guards, the bounded intake, the checkpoint and `repo-health` all
behaved the same.
- **The graph earned its place.** `ask files knowledge/components/idea-board-api.md` found a file
naming a spec the spec did not list (fixed this round); the hand-written use cases agreed with the
code on every other point.
- **Graphify and Archify were already installed** in the copy; no setup ran, and no LLM-backed
Graphify command did either. All fourteen diagrams pass `validate`, `finalize` and the browser
check in Archify 3.2.0.
