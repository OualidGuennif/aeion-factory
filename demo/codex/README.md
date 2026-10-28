# The Codex run

Codex builds the same Idea Board from [`../plan/`](../plan/00-start.md) as the
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

## Starting Codex
1. Trust the project and enable its hooks (`/hooks`), then restart Codex, as in
   `knowledge/operations/agent-compatibility.md`.
2. Open Codex in `demo/` (or at the repository root; [`../plan/00-start.md`](../plan/00-start.md) says
   why both work). Codex loads the root `AGENTS.md` from the git root down.
3. Paste [`../start/codex/START.md`](../start/codex/START.md) as the first message. Its sandbox writes only below `demo/`, so it asks
   before each `git commit`: approve it.

## Results by round

All rounds are complete locally. The owner authorized rounds 01–07 together; no push.
The application is retained in `workspace/app/` (git-ignored), and the gallery opens offline.
The ordinary archive/reset step is deferred so these deliverables remain available for review.

- [Run the app](workspace/app/README.md)
- [Open the architecture gallery](render/index.html)
- [Read the five graph investigations](render/graphify/use-cases.md)
- [Final round journal and evidence](journal/07-architecture.md)

| Round | Result | Tests | Guard refusals | Human help | Feedback |
| --- | --- | --- | --- | --- | --- |
| 00 | Workspace and hooks qualified | 743 factory assertions/tests; 2 skips; 10 hook cases pass, 5 informational | 5 expected synthetic denials; 0 during work | 0 | none new |
| 01 | Fresh and Hono scaffold | 3 pass; app/build/HTTP/factory gates pass | 1 false positive | 1 shared authorization for all rounds | FB-001 |
| 02 | Validated ideas API and KV | 28 pass; app/build/HTTP/factory gates pass | 0 | 0 additional | none new |
| 03 | SSR and enhanced creation | 33 pass; app/build/HTTP/Chrome/factory gates pass | 0 | 0 additional | none new |
| 04 | Atomic votes and sorting | 40 pass; app/build/HTTP/Chrome/factory gates pass | 0 | 0 additional | none new |
| 05 | Indexed tags and bounded search | 49 pass; app/build/HTTP/Chrome/factory gates pass | 0 | 0 additional | none new |
| 06 | Locked non-root Docker and durable volume | 49 pass; build/health/persistence/audit/factory gates pass | 1 false positive | 0 additional | FB-002 |
| 07 | Source-checked graph report and 14 diagrams; API startup regression fixed | 50 pass; 14 validate/render/browser checks; offline gallery, app and rebuilt Docker gates pass | 1 sandbox refusal | 0 additional | FB-003 |

Final validation: formatting, lint, types, 50 app tests and production build pass. Phone/desktop
checks pass in light and dark; unique enhanced creation and vote readbacks pass. Final Docker
readback preserved the exact idea across down/up, ran as UID 1993 and became healthy in 5.52 seconds.
Only the isolated test container/network/volume were removed. No running demo service is left.

Three open framework frictions are documented in [feedback](feedback_for_aeion/README.md).
No base-factory fixes, new global tools, remote CI or push were part of this run. The final journal
states the security/review limits; the workspace remains local, as the brief requires.
