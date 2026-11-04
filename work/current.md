# Current work

Task state only. One entry per open task, newest first. At most 150 lines, 10 per entry.
Finished tasks are deleted: the commit message and knowledge/ keep what matters.
Status: ACTIVE, WAITING-OWNER, MEASURING, BLOCKED, BACKLOG. An entry is `## <title> — <STATUS>`, then the
lines `- Owner decision:`, `- State:`, `- Next:` (with who), `- Blocker:`, `- Evidence:`.

## Security scan findings 2026-11-03 — WAITING-OWNER
- Owner decision: 2026-11-03, a full security check of the repository (Claude Security, whole repository, medium); then a rescan of the unreviewed areas only, never the whole repository again; 2026-11-04, finish the sweep and the panel, then fix everything.
- State: scan 1 at f727090, report verified, 8 findings each confirmed 3/3. F14 HIGH `.dsh/plugins/factory/index.js:31` runs the first `tools/agents/hook.py` found above the session folder (same upward walk in `.opencode/plugins/factory/index.js:23` and `.pi/extensions/factory/index.js:19`). F15-F18 MEDIUM `loops/orchestrator.sh` inner :36, middle :38, watch :43 (web plus `git *`, e.g. `git config core.fsmonitor`), retro :45 (writes `.claude/**`, `gh api`): attacker-writable issue, PR or web text reaches agents with broad git/gh/Write grants. F19 MEDIUM `.claude/hooks/secret_names.py:16` `is_secret()` is case-sensitive (`ENV.LOCAL` opens `.env.local` on APFS). F20 MEDIUM `.github/workflows/outer-loop.yml:31` outsider text plus an issue publish channel. F21 LOW `outer-loop.yml:20` and `pr-review.yml` check out without `persist-credentials: false`.
- Coverage: 10 of 34 researchers returned (no result, no reason). Read: loops, `.github`, `tools/{git-hooks,release,repo-health,loops}`, the native plugins; `tools/agents` for injection only. Unreviewed: `.claude/`, the other `tools/`, `demo/`, `skills/`, the docs, root files and the secrets pass.
- Scan 2 at 6760402, scoped to those areas, report verified, 8 findings: F19 MEDIUM skill-creator eval viewer `generate_review.py:362` takes cross-site POST /api/feedback; F20 MEDIUM `tools/agents/hook.py:119` a padded apply_patch header passes the secret guard; F21 MEDIUM `hook.py:469` grep filter keys are checked for Antigravity only; F22 MEDIUM `guard-bash.py:955` read-only loops allow `gh ... --jq en"v"` (environment dump); F23 MEDIUM `guard-path.py:97` a Grep over a directory reads secret files; F24 LOW `instinct-cli.py:225` import follows redirects to internal addresses; F25 LOW `secret_names.py:16` misses `.git-credentials`, `.credentials.json`, `*.env`, `.dev.vars`, `*.ppk`, `*.jks`, `id_*_sk`, `terraform.tfstate`; F26 LOW `generate_review.py:281` `</script>` in an eval output runs script. 28 of 30 researchers returned: the breadth sweep and the secrets pass hit the session limit.
- Next: all 16 findings and Antigravity's adapter report are fixed and released in v2.0.2 (2026-11-04). The sweep ran 2026-11-04 at 38b2e5f (owner accepted its cost; scan 2's scope, low, attack-surface, secrets pass), report verified, both researchers returned: 1 finding, F1 LOW `skills/claude-plugins-official--plugins-skill-creator-skills-skill-creator/eval-viewer/viewer.html:1292` grader evidence in a title attribute through `escapeHtml` (no quote escaping), 3/3; four candidates refuted. Owner approved 2026-11-04 fixing F1 and releasing 2.0.3: 12 `viewer.html` patches (escapeHtml escapes quotes, every benchmark value escaped) are in `tools/skills/patches.json`, pool refreshed, docs and CHANGELOG updated (uncommitted); verification and the release remain (who: agent).
- Blocker: none.
- Evidence: CLAUDE-SECURITY-20261103-075825/, CLAUDE-SECURITY-20261103-191951/ and CLAUDE-SECURITY-20261104-082150/ CLAUDE-SECURITY-RESULTS.md (git-ignored)

## Connector drift check across all harnesses — ACTIVE
- Owner decision: 2026-11-01, a stale or hand-edited connector must fail a check, not a session; a branch (`main`/`develop`) verifies too, and an adopted project gets an update path that keeps its own content.
- State: shipped through 1.9.1: `tools/agents/adapter-check` (any `--ref`), `tools/agents/dsh-install` and the dsh compaction fixes. 2026-11-03 (owner: smarter updates): `tools/agents/template-update` finds the baseline (`.aeion-factory` or tag inference), updates every changed factory file three-way, prints notes, MAJOR and migrations; live v1.9.4 → v2.0.0 update passed adapter-check and the project's tests.
- Next: v2.0.2 released 2026-11-04. From the factory clone, `tools/agents/template-update --ref v2.0.2 --root <project>` in every adopted project after committing its work (who: agent, owner approves merges; aeion-observability previewed on a clone: 16 updated, 2 real conflicts, AGENTS.md merge) and `tools/agents/dsh-install --tag v2.0.2 --trust <each project>` with a desktop restart (who: owner): from 2.0.2 the plugin refuses a project the profile does not trust.
- Blocker: none.
- Evidence: knowledge/operations/agent-compatibility.md; tools/agents/tests/test_adapter_check.py; tools/agents/tests/test_template_update.py; tools/agents/tests/test_dsh_install.py

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

## Adapt Æion Factory to this project — ACTIVE
- Owner decision: <date>, started from Æion Factory (knowledge/decisions/ADR-001).
- State: the structure is in place; AGENTS.md still describes Æion Factory, not the project.
- Next: write the project's paragraph and build commands in AGENTS.md; walk efficiency/ phases 1 to 7 (who: agent, with the owner's yes per phase).
- Blocker: none.
- Evidence: efficiency/00-EFFICIENCY.md
