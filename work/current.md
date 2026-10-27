# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## Factory audit fixes — ACTIVE
- Owner decision: 2026-10-27, approved the audit plan (findings #1-#7) for one PR.
- State: six commits pushed on task/audit-fixes; all local checks pass.
- Next: open the PR, run pr-review, wait for green CI (who: agent).
- Blocker: none. Owner to decide whether main must require pull requests (direct push was accepted).
- Evidence: branch task/audit-fixes; knowledge/operations/loops.md; knowledge/policies/bounded-intake.md

## Native strict context admission — BLOCKED
- Owner decision: 2026-10-26, attempt native 300k qualification using paid OpenCode Go DeepSeek V4.1 Flash.
- State: primary HTTP denial, 278k-input accounting and over-budget tool continuation exercised in isolation; strict launch still refuses.
- Next: qualify a portable counter, auxiliary calls and the full durable handover/compaction cycle before enabling strict admission.
- Blocker: the experimental counter/profile is not shipped; provider framing and complete native lifecycle coverage remain unqualified.
- Evidence: knowledge/references/opencode-context-qualification.md; knowledge/operations/context-safety.md

## Adapt the Factory to this project — ACTIVE
- Owner decision: <date>, started from Æion Factory (knowledge/decisions/ADR-001).
- State: the structure is in place; AGENTS.md still describes the Factory, not the project.
- Next: write the project's paragraph and build commands in AGENTS.md; walk efficiency/ phases 1 to 7 (who: agent, with the owner's yes per phase).
- Blocker: none.
- Evidence: efficiency/00-EFFICIENCY.md
