# Current work

Updated 2026-11-20. Current facts only; historical evidence is in HANDOVER.md and validation.md.
No final operational Go or actual product feature merge is claimed.

## Feature 006 one-shot merge & Feature 007 spec alignment — READY

- Owner decision: audit Feature `007` (`Content sanitization for user text`) against the merged `006` baseline (`c8e5a372`) and the feature-authoring matrix, align `specs_a.py` (`id: 7`) with the exact `ContentSanitizer` / `ThreadsResource` (`body_html`, `413 {"error": "content_too_large"}`) contract, and merge to `main` before launching `007`.
- State:
  - Feature `006` (`8ea7259e64ab451a9106024d2e5f5b71`, Attempt 1 / Round 0) completed one-shot (`preparer: deepseek-4.1-flash`, `author: glm-5.3-flash`, `39` forwards, S3 gate `passed`, approved by `qwen-3.8-flash` and `claude-haiku-5.5`) and merged to product `main` (`c8e5a372dcd1ca08bc623fc72900d59060fa277b`).
  - Feature `007` (`demo/forum/tools/specs_a.py`, `demo/forum/features/007-content-sanitization-for-user-text.md`) now explicitly specifies `local.aeion.forum.ContentSanitizer.sanitize(String)` (`markdown()`, `html()`), `ContentTooLargeException` (`"content_too_large"` -> HTTP `413 {"error": "content_too_large"}` on `POST /api/threads` without outbox writes), NFC/CRLF/control/zero-width normalization, `4000` Unicode codepoint (including supplementary characters) and `32768`-UTF-8-byte HTML bounds, the attribute-free `p/strong/em/ul/ol/li/blockquote/pre/code` subset, and `"body"` + `"body_html"` on `POST /api/threads`, `GET /api/threads`, and `GET /api/threads/{id}` (no DB schema migration).
- Next: review, merge to `main`, and launch Feature `007` in Cockpit (who: agent, then owner).
- Blocker: none.
- Evidence: [validation](validation.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Cockpit review-stage stepper, Feature 005 lessons & Feature 006 spec alignment — MERGED (PR #56)

- Owner decision: preserve `Review` stage in the Cockpit stepper across reviewer sub-events, align root `.env.example` and `README.md` with the `$5.00` review ceiling, record the three Feature `005` convergence lessons in `knowledge/operations/feature-authoring.md`, and harden Feature `006` (`specs_a.py` -> `006-csrf-protection-on-every-mutation.md` & `MANIFEST.json`) before launch.
- State: merged to `main` in `0e9056f` (PR #56); Feature `006` completed one-shot in `8ea7259e64ab451a9106024d2e5f5b71` (`c8e5a372`).
- Next: tracked by Feature `007` above (who: owner).
- Blocker: none.
- Evidence: [validation](validation.md); [cockpit contract](../knowledge/components/operator-cockpit.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Review cap ($5.00), preflight fallback & Feature 005 unblock — MERGED (PR #55)

- Owner decision: keep full `baseline_context` review quality untouched, raise per-vote `REVIEW_MAX_USD` ceiling/default to `$5.00`, eliminate `0`-forward `BUDGET_STOP` review deadlocks (`a2401f04`), reuse gate-verified `reviewer_failed` artifacts on relaunch, merge to `main`, requalify, and relaunch Feature `005`.
- State: merged to `main` in `6bf51bb` (PR #55); Feature `005` completed end-to-end (`5b4422289e3d4a7dbd47978c8a6f9c80`, authored by `deepseek-4.1-flash`, approved by `qwen-3.8-flash` and `gpt-6-luna`) and merged to product `main` (`38243501a36cbbc538167897bdb07493b99f3c7f`, product PR #21).
- Next: tracked by Feature `006` above (who: owner).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Contract validation, zero-test_error baseline & recovery hardening — MERGED (PR #54)

- Owner decision: eliminate the four contract preparation, verifier reporting, and correction-recovery blind spots exposed by Feature `005` (`5b44fcaa2386` -> `df7c23b47f56` -> `a92b48ae0302`).
- State: merged to `main` in `f65b1f7` (PR #54); preparation and S3 gate passed cleanly on `a2401f04`.
- Next: tracked by review-cap and recovery unblock above (who: agent, then owner).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Feature 004 preparation validation & shape retry — MERGED (PR #50)

- Owner decision: fix why Feature `004` correction round `c9c2c290b5b2` stalled in `held / preparation_unavailable`, add regression coverage, requalify native admission, and keep the live Cockpit ready.
- State: merged to `main` in `8b7314c` (PR #50); Feature `004` completed end-to-end (`4290876ad345`, `39c8336`).
- Next: tracked by Feature `005` above (who: owner).
- Blocker: none.
- Evidence: [validation](validation.md); [factory-flue](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

## Earlier completed milestones (003, Sandbox & Handover resilience) — COMPLETED

- Owner decision: prevent `preparation_negative_control_missing`, handover check-state loss, and `SANDBOX_UNAVAILABLE` collisions on Feature `003`.
- State: PR #45 (`72404ee`) merged to `main`; Feature `003` (`1ab4ce760e8a`, `8bde82c2`) merged to product `main` with [feature authoring guide](../knowledge/operations/feature-authoring.md), `AEION_HANDOVER_CHECK` passed-check propagation (`runner.py`, `factory-checks.ts`, `flue_builder.py`), and OpenShell `SANDBOX_UNAVAILABLE` retry resilience (`setup.py`, `sandbox.py`, `dispatch.py`).
- Next: none; historical evidence in [validation](validation.md) (who: owner).
- Blocker: none.
- Evidence: [validation](validation.md); [execution contract](../knowledge/components/factory-flue.md); [feature authoring](../knowledge/operations/feature-authoring.md).

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
