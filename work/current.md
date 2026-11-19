# Current work

Updated 2026-11-19. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Contract validation, zero-test_error baseline & recovery hardening — READY

- Owner decision: eliminate all four systemic contract preparation, verifier reporting, and correction-recovery blind spots exposed by Feature `005` (`5b44fcaa2386` -> `df7c23b47f56` -> `a92b48ae0302`), merge to `main`, requalify admission, and unblock `005` relaunch.
- State:
  - `validate_acceptance` (`demo/factory/product_checks.py`) rejects masked placeholder literals (`***`, inline `…`) via `preparation_acceptance_masked_literal` and validates JS ESM syntax with `node --check` (`preparation_acceptance_syntax_invalid`); `TaskPreparer` retries both across model families while `acceptance_prompt` warns against mismatched `response.headers` lookups on parsed `api()` helper objects.
  - `run-acceptance.mjs` and `ProductCheckRunner._verify` skip structural `subtestsFailed`/`cancelledByParent` rollups and separate assertion failures from `test_errors` and bounded `error_type` tokens; `_baseline_ok` requires assertion-only baseline failures with zero `test_error` crashes, zero skipped/cancelled/todo tests, and `failed <= contract_assertion_failures` when explicit `test_errors` is absent (keeping registered `001`/`002`/`003`/`014` negative checks distinct), and `_baseline_retry_note` reports failing lines/`error_type`.
  - `flue_session.check_evidence` and `flue_builder.py` retain bounded verifier `test_error` locations and counts; `previous_feature_feedback(..., store=store)` reads `Store` receipts and surfaces supervisor crash summaries; `TaskPreparer.prepare` triggers `reprepare_needed` on objective `0`-assertion `test_error` runtime crashes or normalized conflict tokens across both `gate=failed` and `builder_error`.
  - `_correction_input` and `_judge_and_publish` (`demo/factory/dispatch.py`, `<= 1500` lines) check `acceptance_digest` so unchanged candidates are re-evaluated after `reprepare_needed` updates the contract instead of holding as `correction_unchanged`.
- Next: merge PR to `main`, requalify native admission (`qualify_flue.py` + `factory.admission --activate`), restart Cockpit daemon, and let the owner cancel held build `a92b48ae0302` and relaunch Feature `005` from Catalog (who: agent, then owner).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Feature 004 preparation validation & shape retry — MERGED (PR #50)

- Owner decision: fix why Feature `004` correction round `c9c2c290b5b2` stalled in `held / preparation_unavailable`, add regression coverage, requalify native admission, and keep the live Cockpit ready.
- State: merged to `main` in `8b7314c` (PR #50); Feature `004` completed end-to-end (`4290876ad345`, `39c8336`).
- Next: tracked by Feature `005` above (who: owner).
- Blocker: none.
- Evidence: [validation](validation.md); [factory-flue](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Feature 003 Live Completion, Authoring Playbook & Catalog Alignment — COMPLETED

- Owner decision: prevent `preparation_negative_control_missing` traps across both non-HTTP harness transitions (Feature 003) and general LLM-prepared product contracts (`004`..`100`), and document all accumulated factory feature-authoring rules.
- State: PR #45 (`72404ee`) merged to `main` and activated; Feature `003` (`1ab4ce760e8a4607a47772b47af6feb3`, `deepseek-4.1-flash`, approved by `glm-5.3-flash` and `qwen-3.8-flash`) completed end-to-end and merged to product `main` (`8bde82c2e2ce7f71daa8455ae73a521523788a2a`). Added [feature authoring guide](../knowledge/operations/feature-authoring.md), synced `demo/forum/tools/specs_a.py` with `003`, and aligned 14 Agora P0–P5 specs (`004`..`100`) with baseline verification rules.
- Next: release to `main` via PR #46 and select the next P0 feature(s) in Cockpit.
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Sandbox Provisioning Resilience & Quarkus Lifecycle Hardening — COMPLETED

- Owner decision: prevent recurrence of sandbox EPERM / container naming races, preserve reasoning effort 'max', specify Quarkus injection SPI, and ensure role teardown safety.
- State: `setup.py:normalize_tls_permissions` fixes supervisor EPERM; `sandbox.py` introduces non-colliding attempt hashes (`ae-<root>-<run>-<agents><role>`), bounded retries with backoff, and guarded poisoning; `dispatch.py` treats `SANDBOX_UNAVAILABLE` as retryable ($\le 1500$ lines); `product_checks.py` and Feature 003 spec require `@Override inject(TestInjector)` and owned-role cleanup; tests pass (888/888 demo, 33/33 repo).
- Next: catalog refresh and Feature 003 integration.
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

## Feature 003 Root Cause Debug & Handover Resilience — RESOLVED

- Owner decision: debug why Haiku failed in 3 sessions on Feature 003, preserve reasoning effort 'max', make system resilient against handover traps, and enable reliable relaunch of 003.
- State:
  - Root cause confirmed: in build `557785d03d5f`, Haiku's code changes had fully passed checks (`check.status: passed` at 18:09:37 in session 1). However, fresh handover sessions (2 and 3) initialized in-memory `lastCheck` as `null` because `runner.py` did not pass handover check state to Flue. `finishReminder(null)` forced the model to keep working with `"You have not run run_protected_checks"`. Combined with unguided post-check file edits under reasoning effort `max`, each session hit the 250k context token ceiling (`gate.closed`), exhausting 3 sessions. Furthermore, `flue_builder.py` did not snapshot into `retained` upon normal handover and did not include `handover_limit` in candidate recovery.
  - Fix: `runner.py` passes `AEION_HANDOVER_CHECK` to Flue so resumed sessions preserve passed check state; `factory-checks.ts` initializes `lastCheck` from `AEION_HANDOVER_CHECK` and returns explicit completion instructions upon passing; `flue_builder.py` updates `retained` on each handover and recovers candidates on `handover_limit` (also reflected in `store.py`).
  - Verification: 30/30 Flue tests pass, 9/9 work limit tests pass, 33/33 repo unit tests pass, repo-health passes.
- Next: restart Feature 003 build on cockpit / factory daemon.
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md).

## Factory 3.0 Modernization Plan (All 4 Pillars) — MERGED TO MAIN

- Owner decision: keep thinkingLevel 'max' everywhere across all roles, make system resilient against failure modes, implement OpenShell 0.1.8 qualification and bridge I/O caching, Flue 2.3.0 persistent state and passed-check finish steering, Hindsight 1.2.1 SDK integration with cognitive synthesis fallback, and Langfuse v5.2 enterprise prompt management and multi-dimensional evaluation scores.
- State:
  - Pillar 1: OpenShell 0.1.8 pinned with binary sha256 and OCI image digests (`ghcr.io/nvidia/openshell/sandbox:0.1.8`, `supervisor:0.1.8`); `demo/app/bridge.py` in-memory read cache with mutating invalidation (`write`, `mkdir`, `rm`, `exec`) eliminates subprocess overhead; `demo/app/sandbox.py` supports both 0.1.7 and 0.1.8.
  - Pillar 2: `hindsight-client==1.2.1` pinned; `demo/factory/live_context.py` implements `reflect_cognitive_synthesis` with graceful fail-closed fallback to recall when the provider is `none`.
  - Pillar 3: `demo/flue/src/agents/coder.ts` tracks execution phase, checks run, and last check status via `usePersistentState`; upon passing `run_protected_checks`, steers the model to submit feedback and conclude without unrequested refactoring or handover exhaustion.
  - Pillar 4: `demo/factory/prompts.py` centralizes system prompts for author, reviewer, and preparer with deterministic local templates and Langfuse Prompt Management fallback; `demo/app/scores.py` computes multi-dimensional scores (`factory.check.acceptance`, `factory.review.consensus`, `factory.budget.efficiency`, `factory.cache.hit_ratio`) without polluting synthetic demo verification.
- Next: catalog refresh for next features on main (who: agent).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [docker demo](../knowledge/components/docker-demo.md).

## Trusted product CI and PostgreSQL/React — PARTIAL

- Owner decision: workers may propose dependency transitions without changing their evaluator; trusted CI updates use separate publisher/release credential roles.
- State: product CI PR 5 is merged as `e55b820ca4534738283df1674ba80be43ec03fa5` with all six exact-head checks green. Observer adapters 001/002/014, isolated unit PostgreSQL 17, migration/import/restore and frozen React build/test are implemented and natively qualified.
- Next: implement product 014 React and 002 PostgreSQL through actual workers after 001 integration (who: agent).
- Blocker: qualified adapters and CI are not implemented product migrations or deployed React; preserve canonical checkout and local data.
- Evidence: https://github.com/OualidGuennif/aeion-autonomous-forum/pull/5 ; [maintainer tool](product-ci-adapters-2026-11-05/maintain.py).

## Actual environments and cockpit links — OPEN

- Owner decision: provide real staging/production links and readable implementation stages; technical-only features may explicitly have no dedicated demo.
- State: the cookie-filtering product proxy is tested locally; the cockpit shows Staging and Production as "Not deployed yet" and omits the synthetic canary drill.
- Next: wire checked product artifacts to isolated environments, prove readiness and exact source identity, then expose verified links (who: agent).
- Blocker: no real staging or production deployment receipt exists yet; do not relabel the unverified local container as delivered main.
- Evidence: [Cockpit contract](../knowledge/components/operator-cockpit.md); [product proxy](../demo/factory/product_proxy.py).
