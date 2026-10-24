# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## Reliable verification and portable file discovery — ACTIVE
- Owner decision: 2026-10-24, approved the three core research-plan corrections in chat.
- State: implementing explicit failures, portable traceability and hook error handling.
- Next: add regression fixtures, implement the narrow fixes, run checks and a fresh local review (agent).
- Blocker: no remote publication authorized; local verification uses the inspected baseline.
- Evidence: tools/knowledge/tests/test_doc_links.py; tools/repo-health/tests/test_repo_health.py; .claude/hooks/test_hooks.py.

## Adapt the Factory to this project — ACTIVE
- Owner decision: <date>, started from Æion Factory (knowledge/decisions/ADR-001).
- State: the structure is in place; AGENTS.md still describes the Factory, not the project.
- Next: write the project's paragraph and build commands in AGENTS.md; walk efficiency/ phases 1 to 7 (who: agent, with the owner's yes per phase).
- Blocker: none.
- Evidence: efficiency/00-EFFICIENCY.md
