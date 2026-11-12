# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG. An entry is `## <title> — <STATUS>`, then the
lines `- Owner decision:`, `- State:`, `- Next:` (with who), `- Blocker:`, `- Evidence:`.

## Æion Template 4.0.0: back to the essence, framework optional — ACTIVE
- Owner decision: 2026-11-12, rename to aeion-template (no compatibility), remove the embedded AxiomSpec engine, demo/ and efficiency/, framework mode optional and off by default (the API address is the switch), a blocking doc gate, context rule 340k/390k.
- State: committed on develop: 340k/390k (1ec5a2b), removals (03d16d2), rename (860ffe8), owner's settings (6fba16b), doc gate (live in Claude Code: refused an unread-doc edit, allowed it after the reads).
- Next: framework client tools/framework/axiom-api and @req briefs; README/AGENTS rewrite; review; release PR (who: agent; the owner renames the GitHub repository and approves the push).
- Blocker: none.
- Evidence: CHANGELOG.md Unreleased; knowledge/components/framework-mode.md; knowledge/components/doc-gate.md; /Users/wallseven/.claude/plans/kind-wobbling-star.md

## Grok adapter — ACTIVE
- Owner decision: 2026-11-06, release the Grok adapter as 2.1.1. This replaces the same-day decision to keep it on a local `grok` branch.
- State: guards run from `.grok/hooks/template.json`. The Claude budget hook ignores a Grok envelope and a transcript named `updates.jsonl` or `chat_history.jsonl`. The context size is `signals.json` `contextTokensUsed`. The path guard accepts `target_file` and `target_directory`. Not live-qualified.
- Next: after the 2.1.1 release, qualify a live Grok session (`cat .env` refused, an edit names its doc, a new session stays RUNNING) (who: owner).
- Blocker: none.
- Evidence: knowledge/operations/agent-compatibility.md; knowledge/operations/context-safety.md; .claude/hooks/test_hooks.py; tools/context/tests/test_budget.py

## Connector drift check across all harnesses — ACTIVE
- Owner decision: 2026-11-01, a stale or hand-edited connector must fail a check, not a session; a branch (`main`/`develop`) verifies too, and an adopted project gets an update path that keeps its own content.
- State: shipped through 1.9.1: `tools/agents/adapter-check` (any `--ref`), `tools/agents/dsh-install` and the dsh compaction fixes. 2026-11-03 (owner: smarter updates): `tools/agents/template-update` finds the baseline (`.aeion-template` or tag inference), updates every changed template file three-way, prints notes, MAJOR and migrations; live v1.9.4 → v2.0.0 update passed adapter-check and the project's tests.
- Next: v2.1.0 released 2026-11-06 (ub-mode build principles, template-update hint; 2.0.2/2.0.3 the security fixes). From the template clone, `tools/agents/template-update --ref v2.1.0 --root <project>` in every adopted project after committing its work (who: agent, owner approves merges; aeion-observability is on v2.0.3 as of 2026-11-05: 28/28 connectors match, its own session resolved the 7 merges, not committed there yet) and `tools/agents/dsh-install --tag v2.1.0 --trust <each project>` with a desktop restart (who: owner): from 2.0.2 the plugin refuses a project the profile does not trust.
- Blocker: none.
- Evidence: knowledge/operations/agent-compatibility.md; tools/agents/tests/test_adapter_check.py; tools/agents/tests/test_template_update.py; tools/agents/tests/test_dsh_install.py

## Golden task set — MEASURING
- Owner decision: 2026-10-31, start the local evaluation harness, then approve the twelve candidate tasks proposed with it.
- State: eleven tasks in `tools/evals/tasks/`, five implementation and six process, all at "not run yet"; the one Pi baseline (architecture-answer, 2026-10-31) stays in results.jsonl, its task left with the embedded engine in 4.0.0.
- Next: one baseline per harness on the same fixed commit, then compare (who: owner; an agent prepares each run).
- Blocker: one harness measured, so no across-harness comparison is possible yet.
- Evidence: knowledge/operations/evals.md; tools/evals/results.jsonl

## Live Devin, Droid, Antigravity and Pi hook qualification — WAITING-OWNER
- Owner decision: 2026-10-27, support Devin, Droid and Antigravity; 2026-10-28, Pi 1.4.0; adapters use documented, not live-run, payloads.
- State: Devin merged in #12, Droid in #13, Antigravity in task/antigravity, Pi on develop. Pi guards ran live headless on 2026-11-01. 1.9.2 fixed Pi's headless 250k crash (clean stop); `tools/agents/run pi rpc` then compacted and resumed live at 288,668 tokens (2026-11-02), so headless auto-compaction is available through the RPC runner while print mode keeps the clean stop; dsh headless and OpenCode 2.2.0 compacted live at 250k/272k with verified receipts.
- Next: run the remaining qualification steps with Devin CLI, Droid and agy (who: owner); Pi's remaining item is a live TUI settlement-compaction test (the RPC path is qualified).
- Blocker: Devin/Droid/Antigravity CLIs are not in the agent's container; Pi print mode cannot compact (the clean stop ships, the RPC runner is the headless path).
- Evidence: knowledge/operations/agent-compatibility.md; .pi/README.md; .opencode/README.md; tools/agents/pi-rpc

## Native strict context admission — BLOCKED
- Owner decision: 2026-10-26, attempt native 300k qualification using paid OpenCode Go DeepSeek V4.1 Flash.
- State: primary HTTP denial, 278k-input accounting and over-budget tool continuation exercised in isolation; strict launch still refuses.
- Next: qualify a portable counter, auxiliary calls and the full durable handover/compaction cycle before enabling strict admission.
- Blocker: the experimental counter/profile is not shipped; provider framing and complete native lifecycle coverage remain unqualified.
- Evidence: knowledge/references/opencode-context-qualification.md; knowledge/operations/context-safety.md

## Adapt Æion Template to this project — ACTIVE
- Owner decision: <date>, started from Æion Template (knowledge/decisions/ADR-001).
- State: the structure is in place; AGENTS.md still describes Æion Template, not the project.
- Next: write the project's paragraph and build commands in AGENTS.md; walk the adopt skill's phases 1 to 7 (who: agent, with the owner's yes per phase).
- Blocker: none.
- Evidence: .claude/skills/adopt/SKILL.md
