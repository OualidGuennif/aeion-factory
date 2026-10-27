# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## Live Devin and Droid hook qualification — WAITING-OWNER
- Owner decision: 2026-10-27, support Devin and Droid; adapters merged with documented, not live-run, payloads.
- State: Devin in PR #12, Droid in task/droid-and-naming; no live run of either yet.
- Next: run the qualification steps with Devin CLI and Droid and record the result (who: owner).
- Blocker: neither CLI is in the agent's container.
- Evidence: knowledge/operations/agent-compatibility.md

## Review fixes: secrets, closure, hooks, pins — ACTIVE
- Owner decision: 2026-10-27, apply all findings of the full repository review.
- State: task/review-fixes: one secret list with glob resolution, closure parse and local-mode checkpoint, MultiEdit/NotebookEdit hooks, sign-off input, hash-pinned requirements, doc fixes.
- Next: pass the checks, open the PR, fresh review, merge after PR #14 (who: agent).
- Blocker: none; codeload.github.com returns 403 here, so the hash-checked install is proven in CI.
- Evidence: knowledge/policies/security.md; knowledge/operations/context-safety.md

## Main branch protection — WAITING-OWNER
- Owner decision: 2026-10-27, protect main as knowledge/operations/github-protection.md describes.
- State: the agent's GitHub tools cannot change branch protection; the settings must be applied by the owner.
- Next: owner applies the rule in Settings → Rules/Branches and reads it back with the API (who: owner).
- Blocker: no branch-protection access from the agent session.
- Evidence: knowledge/operations/github-protection.md

## Native strict context admission — BLOCKED
- Owner decision: 2026-10-26, attempt native 300k qualification using paid OpenCode Go DeepSeek V4.1 Flash.
- State: primary HTTP denial, 278k-input accounting and over-budget tool continuation exercised in isolation; strict launch still refuses.
- Next: qualify a portable counter, auxiliary calls and the full durable handover/compaction cycle before enabling strict admission.
- Blocker: the experimental counter/profile is not shipped; provider framing and complete native lifecycle coverage remain unqualified.
- Evidence: knowledge/references/opencode-context-qualification.md; knowledge/operations/context-safety.md

## Adapt Æion Factory to this project — ACTIVE
- Owner decision: <date>, started from Æion Factory (knowledge/decisions/ADR-001).
- State: the structure is in place; AGENTS.md still describes Æion Factory, not the project.
- Next: write the project's paragraph and build commands in AGENTS.md; walk efficiency/ phases 1 to 7 (who: agent, with the owner's yes per phase).
- Blocker: none.
- Evidence: efficiency/00-EFFICIENCY.md
