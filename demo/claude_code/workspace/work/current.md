# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.


## Idea Board rounds 02–07 — ACTIVE
- Owner decision: 2026-10-28, build the Idea Board from the briefs `../../01-scaffold.md` … `07-architecture.md`, one round each.
- State: round 01 (scaffold, `/api/health`) done; tests and smoke pass.
- Next: round 02, the ideas API on Deno KV (who: agent).
- Blocker: none.
- Evidence: `knowledge/components/idea-board-api.md`; `cd app && deno task test`.
