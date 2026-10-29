# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## demo/ Idea Board run and feedback for Æion — ACTIVE
- Owner decision: 2026-10-28, Claude Code builds the Idea Board in a git-less copy (demo/claude_code/workspace), journals each round, files feedback, fixes small ones in the base.
- State: briefs in demo/plan/; rounds 00–02 done (2396a52, 64a466b); FB-006 fixed in 2c2fb1d; only demo/<harness>/workspace/ is git-ignored (FB-001–009); rounds 03–04 done and visually approved (page + island; votes); round 05 done and approved (tags, search, 72 tests); round 06 done (Docker, 5 container checks); round 07 done (Graphify, 14 Archify diagrams, gallery; FB-010); base fixes FB-002/004/005/007/008/009/010 committed (9d4f78c..87a27b0); READMEs, app snapshot (result/), demo/codex/ ready (ce7c8c6); docs/diagrams.html (cdd6991). Pi run (2026-10-29): rounds 00–06 committed on develop (451e9e0, 19ad04d, 1a47291, then one commit each for 03–06), 79 tests, FB-001 open; round 07 in progress (10 diagram JSONs written, 1 finalized, 3 sequences and the gallery to go) — closed at 250k into work/handovers/pi-ab8c2bed0c9aecea9e8083610b4ebf1ddba677d4.md.
- Next: OpenCode run done (rounds 00–07, FB-001–003); Codex rerun rounds 00–06 committed (c422ead..0cf38b7), round 07 in progress after a stalled compaction (fixed in 39da8c4); then Claude Code run 2, Pi and dsh from demo/start/; every workspace synced to 1.5.0 on 2026-10-29 (who: owner). Pi resumes round 07 from its handover.
- Blocker: none.
- Evidence: work/handovers/35c6f26d-3a08-48c8-8457-2cb97c7285df.md; work/handovers/pi-ab8c2bed0c9aecea9e8083610b4ebf1ddba677d4.md

## Live Devin, Droid, Antigravity and Pi hook qualification — WAITING-OWNER
- Owner decision: 2026-10-27, support Devin, Droid and Antigravity; 2026-10-28, Pi 1.4.0; adapters use documented, not live-run, payloads.
- State: Devin merged in #12, Droid in #13, Antigravity in task/antigravity, Pi on develop; no live run of any yet.
- Next: run the qualification steps with Devin CLI, Droid, agy and Pi and record the result (who: owner).
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
