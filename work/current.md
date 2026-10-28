# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## Release v1.3.0 — WAITING-OWNER
- Owner decision: 2026-10-28, merge commits allowed and linear history off on main (applied via gh api).
- State: #19 merged as 34c0b2e (CI and Architecture refresh green), tag v1.3.0 pushed, develop fast-forwarded; the GitHub release page is not created (the agent's permission mode refused gh release create).
- Next: gh release create v1.3.0 --title v1.3.0 --notes "$(tools/release/release --notes 1.3.0)", then delete this entry (who: owner, or agent once allowed).
- Blocker: none.
- Evidence: knowledge/operations/github-protection.md; .claude/skills/ship/SKILL.md

## Live Devin, Droid and Antigravity hook qualification — WAITING-OWNER
- Owner decision: 2026-10-27, support Devin, Droid and Antigravity; adapters use documented, not live-run, payloads.
- State: Devin merged in #12, Droid in #13, Antigravity in task/antigravity; no live run of any yet.
- Next: run the qualification steps with Devin CLI, Droid and agy and record the result (who: owner).
- Blocker: neither CLI is in the agent's container.
- Evidence: knowledge/operations/agent-compatibility.md

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
