# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## Audit fixes and agent compatibility — ACTIVE
- Owner decision: 2026-10-25, fix the full audit, protect AEion main branches, add Codex/OpenCode and document setup.
- State: seven main branches protected; audit/review regressions corrected; native V2 qualification in progress.
- Next: implement adapters and narrow fixes, validate real integrations, review and deliver by PR.
- Blocker: strict native pre-request 300k admission remains unqualified separately below.
- Evidence: knowledge/operations/agent-compatibility.md; knowledge/components/factory-architecture.md

## Native strict context admission — BLOCKED
- Owner decision: 2026-10-25, integrate context safety and architecture maintenance while preserving the Factory core.
- State: checkpoint profile implemented; no absolute pre-request 300k ceiling is claimed; strict launch refuses.
- Next: qualify a supported before-every-request admission boundary and a controlled native long-session run.
- Blocker: no complete native pre-request admission boundary is qualified; observed-hook guards do not establish an absolute ceiling.
- Evidence: knowledge/operations/context-safety.md; knowledge/components/factory-architecture.md

## Adapt the Factory to this project — ACTIVE
- Owner decision: <date>, started from Æion Factory (knowledge/decisions/ADR-001).
- State: the structure is in place; AGENTS.md still describes the Factory, not the project.
- Next: write the project's paragraph and build commands in AGENTS.md; walk efficiency/ phases 1 to 7 (who: agent, with the owner's yes per phase).
- Blocker: none.
- Evidence: efficiency/00-EFFICIENCY.md
