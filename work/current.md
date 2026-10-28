# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG.

## demo/ Idea Board run and feedback for Æion — ACTIVE
- Owner decision: 2026-10-28, Claude Code builds the Idea Board in a git-less copy (demo/claude_code/workspace), journals each round, files feedback, fixes small ones in the base.
- State: briefs in demo/plan/; rounds 00–02 done (2396a52, 64a466b); FB-006 fixed in 2c2fb1d; only demo/<harness>/workspace/ is git-ignored (FB-001–009); rounds 03–04 done and visually approved (page + island; votes); round 05 done and approved (tags, search, 72 tests); round 06 done (Docker, 5 container checks); round 07 done (Graphify, 14 Archify diagrams, gallery; FB-010); base fixes FB-002/004/005/007/008/009/010 committed (9d4f78c..87a27b0); READMEs, app snapshot (result/), demo/codex/ ready (ce7c8c6); docs/diagrams.html (cdd6991).
- Next: OpenCode run rounds 00–04 committed (22ba54d, 3058484, a3e491f, 9d7d7ca, 2829d56), round 05 green but uncommitted, checkpoint verified for a compaction; after recovery finish rounds 05–07 and update demo/opencode/README.md; Codex rerun tomorrow from the reset demo/codex/ after a /hooks and `cat .env` check; then Claude Code run 2 and Pi from demo/start/ (who: owner).
- Blocker: none.
- Evidence: work/handovers/35c6f26d-3a08-48c8-8457-2cb97c7285df.md

## One context rule for every harness — MEASURING
- Owner decision: 2026-10-28, Codex, OpenCode and Pi get Claude's 250k closure and verified handover; 300k forces handover and compaction again, never a stop.
- State: shared `apply_usage` in tools/context/budget.py, usage readers in tools/agents/hook.py, Pi and OpenCode compact themselves; factory-tests pass; demo/*/workspace copies synced.
- Next: on the next OpenCode 2.2.0 and Pi runs, confirm step tokens reach the hook and self-compaction fires once at 250k (who: owner runs, agent reads the journal).
- Blocker: none.
- Evidence: knowledge/operations/context-safety.md

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
