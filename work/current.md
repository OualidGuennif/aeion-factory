# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG. An entry is `## <title> — <STATUS>`, then the
lines `- Owner decision:`, `- State:`, `- Next:` (with who), `- Blocker:`, `- Evidence:`.

## dsh/Pi terminal stop and the 300k checkpoint deadlock — WAITING-OWNER
- Owner decision: 2026-10-31, ship Fix 1 and the 300k stopgap in 1.8.2, then merge, tag and publish after a green CI.
- State: released as v1.8.2 (tag on e5981b3, GitHub release published, main and develop in sync). dsh and Pi end a terminal stop with its reason instead of steering it; at 300k a failing check no longer blocks compaction, code stays editable afterwards and the closure stays owed until a verified checkpoint. Live headless dsh on a stub that always stops: the fixed adapter sent 1 Stop and exited, the pre-fix adapter 51 Stops in 90s and never exited.
- Next: update the live plugin copy the desktop profile loads (`~/.dsh/profiles/desktop/aeion-factory` symlinks `/Users/wallseven/Desktop/Showcase/my-app/.dsh/plugins/factory`) and restart the app; its `index.js` still holds the broken `invoke(...)` line, so the app has no hooks (who: owner).
- Blocker: that copy is outside this repository, so the release cannot repair it.
- Evidence: CHANGELOG.md 1.8.2; knowledge/operations/context-safety.md; knowledge/operations/agent-compatibility.md

## Golden task set — MEASURING
- Owner decision: 2026-10-31, start the local evaluation harness, then approve the twelve candidate tasks proposed with it.
- State: twelve tasks in `tools/evals/tasks/`, six implementation and six process; one baseline is recorded (architecture-answer on pi, success, 0.9 minutes) and eleven still say "not run yet"; `report` renders one row.
- Next: one baseline per harness on the same fixed commit, then compare (who: owner; an agent prepares each run).
- Blocker: one harness measured, so no across-harness comparison is possible yet.
- Evidence: knowledge/operations/evals.md; tools/evals/tasks/architecture-answer/BASELINE.md

## demo/ Idea Board run 2 — WAITING-OWNER
- Owner decision: 2026-10-28, each harness builds the Idea Board in a git-less copy, journals each round and files feedback; 2026-10-29, the run 1 wrap-up plan and run 2 driven by one orchestrator session.
- State: run 1 done and archived for all five harnesses (demo/<h>/archive/run-01/, comparison in demo/README.md); its feedback fixed in the factory (c3f586f, fd288e9) or in the run 2 brief (e1f30ad); orchestrator brief in cfc92e1.
- Next: run 2 is planned for the week of 2026-11-02, not before; on the owner's go, a Claude Code session runs demo/start/orchestrator/START.md, one harness at a time (who: owner, then agent).
- Checked 2026-10-29: the four run 1 galleries load 14/14 previews from file:// in headless Chrome, viewer opens, pages and closes; OpenCode is `opencode2` 2.2.0.
- Blocker: none.
- Evidence: demo/README.md; demo/start/orchestrator/START.md; work/handovers/b5bf5c06-1101-47fa-a0b7-f0ca1ac15381.md

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
