---
type: Runbook
title: "Authoring factory-compatible features"
description: "Canonical rules and battle-tested lessons for writing Agora features so preparation, negative control, OpenShell builds, and independent review succeed cleanly."
status: stable
review_after: 2027-02-13
sources:
  - resource: ../../demo/forum/PLAN.md
    title: "Agora product contract and catalog rules"
  - resource: ../../demo/forum/ARCHITECTURE.md
    title: "Approved Quarkus, PostgreSQL, and React architecture"
  - resource: ../../demo/forum/tools/generate_features.py
    title: "Catalog validator and Markdown renderer"
  - resource: ../../demo/factory/preparation.py
    title: "Task freezing, baseline negative-control retries, and preparation guards"
  - resource: ../../demo/factory/product_checks.py
    title: "Product acceptance prompt, registered transitions, and Docker check runner"
  - resource: ../../demo/factory/product_harness.py
    title: "Isolated JUnit harness oracle for Feature 003"
  - resource: ../../demo/factory/store.py
    title: "Preparation evidence validation and admission state machine"
  - resource: ../../demo/factory/flue_builder.py
    title: "Author context limits, handover check propagation, and candidate recovery"
  - resource: ../../demo/app/sandbox.py
    title: "OpenShell sandbox isolation and provisioning retries"
  - resource: ../../demo/flue/src/tools/factory-checks.ts
    title: "Protected check state and passed-check completion guidance"
---

# Authoring factory-compatible features

[Operations index](index.md) · [Flue factory execution](../components/factory-flue.md) · [Factory architecture](../components/factory-architecture.md) · [Specs first](../policies/specs-first.md)

Every feature run goes through four deterministic gates before merge: **catalog freeze**, **independent preparation + baseline negative control**, **OpenShell tier-3 authoring (`run_protected_checks`)**, and **two-vote independent review**. Features designed without those four gates in mind fail cleanly (fail-closed) rather than passing silently.

## 1. Where features live and how they freeze

1. **Edit Python specs, never generated Markdown.** Canonical definitions live in `demo/forum/tools/specs_a.py` through `specs_f.py`. After any edit, regenerate `demo/forum/features/` and `MANIFEST.json` and verify there is zero drift:
   ```bash
   python3 -B demo/forum/tools/generate_features.py
   python3 -B demo/forum/tools/generate_features.py --check
   python3 -B -m unittest discover -s demo/forum/tools -p 'test_*.py' -v
   ```
2. **Satisfy static catalog and `freeze_task()` invariants:**
   - Stable numeric ID (`001`..`100`), unique title slug, `tier: 3`, valid `area` and `size` (`S`, `M`, `L`).
   - `phase` in `P0`..`P5` with acyclic `depends_on` referencing only features in the same or an earlier phase.
   - Between `2` and `4` concrete delivery steps (`<= 220` characters each) and all mandatory spec sections (`goal`, `scope`, `delivery`, `security`, `accept` with `- [ ] ` items, `test`, `out`).
   - `write_paths` are literal relative paths (no globs, `.` or `..`) inside `demo/forum-app/`, `demo/forum-web/`, `demo/forum-docs/`, or `knowledge/components/`. Regular Java tasks are narrowed by `preparation.py` to Java main/test/resources, `test/resources/`, `demo/forum-web/`, `demo/forum-docs/`, and `knowledge/components/`; Gradle/npm dependency changes require explicit transition adapters.
   - `parallel: true` specs must have strictly disjoint `write_paths` and cannot reserve full product roots.
   - Markdown byte size must stay `<= 12,000` bytes ( regular non-symlink UTF-8 file), matching both `catalog_digest` and `architecture_digest`.
   - Superseded stack names (`FastAPI`, `pytest`, `extra=forbid`, `no client framework`, `without JavaScript`) are rejected at generation time.

## 2. Design acceptance observability upfront (avoiding `preparation_negative_control_missing`)

Before an author starts, `TaskPreparer.prepare()` executes the frozen `acceptance.mjs` contract against the **untouched product baseline (`origin/main`)**. If all assertions pass on baseline, preparation is refused (`preparation_negative_control_missing`).

| Feature kind | How the factory verifies it | Authoring rule |
| --- | --- | --- |
| **User-facing / API / Web (`004`+)** | LLM preparer writes Node 26 / `fetch` / Playwright 1.64.1 black-box tests against `http://127.0.0.1:8080`. It has **no** Java classes, DB credentials, shell, or host files. | Specify at least one concrete **externally observable HTTP or browser delta** (route, status code, JSON shape, DOM state, auth/CSRF refusal) that **does not already exist** on baseline. |
| **Pure internal transition / SPI / build seed (`001`, `002`, `003`, `014`)** | Registered static contract in `demo/factory/transitions/<kind>/` plus supervisor-owned oracle (`product_checks.py`, `product_harness.py`). | Do **not** leave a pure internal/JUnit feature on LLM HTTP preparation if all HTTP probes already pass on baseline. Register a supervisor oracle + transition files and add the ID across `product_checks.py`, `preparation.py`, `store.py`, and `flue_qualification.py`. |

Although `TaskPreparer.prepare()` clears and retries both contract-shape failures (`preparation_acceptance_*` with `_contract_retry_note`) and baseline-passing contracts (`_baseline_retry_note`) across up to `3` distinct model families with diagnostic feedback, unambiguous observable deltas prevent wasting preparation attempts altogether.

## 3. Battle-tested lessons from the factory (preventing deadlocks and hallucinations)

Every rule below comes directly from production incidents resolved in Features `001`–`005`:

1. **Never contradict inherited transport and security guards:**
   - **16 KiB HTTP body limit:** Quarkus HTTP transport rejects payloads `> 16 KiB` with `HTTP 413` before application validators run. Do not write acceptance requirements expecting `400` or `422` on `20 KiB` payloads; `acceptance_prompt` enforces `413` above `16 KiB` and `422` (`{"error": "validation_failed", "fields": [...]}`) or `400` on bounded invalid JSON.
   - **CSRF on cookie mutations:** Committed endpoints enforce `X-CSRF-Token` (returned as `"csrf"` by `/api/auth/login`) on authenticated `POST`/`PUT`/`DELETE` requests carrying session cookies. Any authenticated mutation spec or example must preserve CSRF protection.
   - **Bind emitted HTTP wire attributes (`Set-Cookie` `Max-Age`, `Secure`) to configured bounds and scheme:** When a feature makes lifetimes configurable (such as idle/absolute session timeouts with a `900s` default) or scheme-dependent (`Secure` over HTTPS, omitted over plain HTTP), emitted cookie/header attributes (`Max-Age`) must reflect the effective configured lifetime rather than staying hardcoded to `900`.
2. **Separate internal test fixtures from live HTTP behavior:**
   - Frozen Java `Clock`, seeded `Random`, and disposable DB fixtures are **JUnit/Quarkus test harness concerns**, never global frozen timestamps across independent live HTTP requests. State the boundary explicitly in `scope` and `out` so preparers do not invent cross-request frozen-clock HTTP tests (which force authors into out-of-scope clock hacks).
3. **Specify exact framework SPI signatures, eager startup checks, and resource ownership:**
   - Vague SPI wording leads authors to wrong overloads (for example `inject(Object)` instead of Quarkus `QuarkusTestResourceLifecycleManager`'s `@Override public void inject(TestInjector testInjector)`). Write the exact Java SPI / package contract in `scope`.
   - **Force eager startup validation for `@ApplicationScoped` config beans in `StartupChecks`:** Quarkus normal-scoped (`@ApplicationScoped`) beans are lazy client proxies whose constructor `@ConfigProperty` validation only runs on first method invocation. Any new validated config/lifetime/secret bean must be invoked eagerly in `StartupChecks.onStart(@Observes StartupEvent)` (e.g., `bean.selfCheck()`) so invalid configuration fails boot before serving requests.
   - Remember Quarkus config ordinals: `QuarkusTestResourceLifecycleManager` system properties (`ordinal 400`) override `@QuarkusTestProfile` config overrides (`ordinal 275`).
   - Ephemeral test teardown must track resources (databases, roles) **created by that instance only** and refuse unmarked DBs or unapproved hostnames **before DDL** via explicit refusal (never falling back to raw `SQLException` or dropping pre-existing roles on setup failure).
4. **Keep specs minimal, single-feature, and strictly scoped:**
   - For product runs, `TaskPreparer` exposes committed `@Path`, `@Provider`, and `@ApplicationScoped` Java interfaces (`<= 100 KB` per file, preserving `static final` constants in summaries) from `base_sha`, while `acceptance_prompt` enforces dummy test passwords `>= 12` characters (never `***` or `…`) and warns against helper mismatches such as reading `response.headers` on parsed `api()` objects; `validate_acceptance` rejects masked literals and ESM syntax errors (`node --check`), and `_baseline_ok` requires assertion-only baseline failures with zero `test_error` crashes. Independent review also receives read-only unchanged base context (`baseline_context`) within envelope headroom so filters such as `CsrfGuard` are visible without editing them. Do not mention unrelated endpoints or global settings lists in `accept` or `test`; doing so causes preparers to assert unrelated pagination/edge behaviors, forcing authors into out-of-scope edits that reviewers rightfully reject (`reviewer_rejected` / `correction_unchanged`).
   - **Lead `## Acceptance checks` with the new baseline-failing HTTP delta and exclude future-phase subsystems:** If a guard (such as `CsrfGuard`) already exists on `origin/main`, listing only its existing behavior in `## Acceptance checks` causes `TaskPreparer` to write a contract that passes on baseline (`preparation_negative_control_missing`). Put the new baseline-missing endpoint or behavior (`GET /api/auth/csrf`) in the first bullet of `## Acceptance checks`, and exclude directories or subsystems introduced in later features (`demo/forum-web/` in `014`, broker agent tokens in `053`) from `write_paths` and `scope` (placing them in `## Out of scope`).
5. **Respect author budget, handover, and reviewer limits:**
   - Authors run with `thinkingLevel: 'max'`, a `250k` native context cap, and up to `3` handover sessions. `AEION_HANDOVER_CHECK` carries passed check state across handovers and `factory-checks.ts` instructs the model to finalize (`submit_feedback`) immediately once `run_protected_checks` passes, rather than spending remaining context polishing Markdown.
   - Keep `write_paths` and required deliverables focused (`S`/`M` effort) so one or two focused slices pass unit checks, protected black-box acceptance, and independent two-vote review well inside the session/token budget.

## 4. Checklist before launching a new or updated feature

1. Run catalog generation & check (`generate_features.py --check` + `demo/forum/tools` tests).
2. Confirm every item in `## Acceptance checks` is either:
   - black-box testable via `http://127.0.0.1:8080` (HTTP + Chromium/Playwright) and fails on untouched `origin/main`, **or**
   - covered by a registered transition oracle in `demo/factory/transitions/`.
3. Confirm no assertion conflicts with the `16 KiB` `HTTP 413` guard, cookie `X-CSRF-Token`, or `422` validation envelope.
4. Confirm any new internal Java SPI signature or teardown safety invariant is named explicitly in `**Scope:**` and `## Invariants`.
5. If factory protocol files (`demo/factory/`, `demo/app/`, `demo/flue/`, `demo/openshell/`) changed while implementing an adapter/oracle, run repository checks, merge to `main`, and requalify live admission (`(cd demo && .local/venv/bin/python -m factory.admission --activate)`), then restart the Cockpit daemon.

## 5. Quick diagnosis when a build goes on hold

| Hold / Stop reason | Meaning | Fix path |
| --- | --- | --- |
| `preparation_acceptance_*` | Proposed `acceptance.mjs` failed static ESM validation (missing assertions, `.skip`/`.todo`/`.only`, masked literals like `***`/`…`, or `node --check` syntax errors) across up to 3 retryable preparer families. | Inspect `proposed-acceptance.json` and check logs; `validate_acceptance` accepts direct, destructured, and named `node:assert/strict` assertions and ignores prose comments/strings, while cancelling and relaunching retries cleanly. |
| `preparation_negative_control_missing` | Prepared `acceptance.mjs` passed all assertions or crashed with runtime `test_error`s on untouched baseline after retries. | Tighten the feature spec's externally observable baseline delta (`specs_*.py`), or add a registered transition oracle if pure internal SPI/build work. |
| `preparation_budget_stop` | The next request did not fit the per-model preparation cap and preparation could not finish through the bounded recovery path. | Check measured spend and the last preparer in Build evidence. See [preparation admission and recovery](../components/factory-flue.md). |
| `preparation_daily_budget_unavailable` | The forum purse could not reserve the next preparation attempt. | Check the daily forum purse for settled and reserved amounts. |
| `USAGE_UNKNOWN` in a review vote | The reviewer stopped with incomplete accounting. | Inspect the existing reservation and the [review retry contract](../components/factory-flue.md) before taking action. |
| `reviewer_rejected` / `correction_unchanged` | Author hit a buggy/out-of-scope/crashing contract under the same `acceptance_digest` or reviewers flagged out-of-scope edits. | Do not edit `acceptance.mjs` manually; inspect `receipt.feedback` / `circuit.votes` / `test_errors`. `reprepare_needed` auto-triggers on `0`-assertion verifier `test_error` crashes or normalized `FROZEN_ACCEPTANCE.mjs`/policy conflicts (`gate=failed` or `builder_error`), `dispatch.py` re-judges unchanged candidates once `acceptance_digest` updates, `two_vote_review` substitutes once on `0`-forward preflight `BUDGET_STOP`/`CONTEXT_UNKNOWN` refusals (excluded on retry), and `prior_candidate` reuses gate-passed `reviewer_failed` files on relaunch. |
| `SANDBOX_UNAVAILABLE` | Docker/OpenShell TLS permissions or stale container collision. | Ensure `openshell/setup.py` `normalize_tls_permissions` ran and wait/clear stale gateway sandboxes; `dispatch.py` retries transient stops automatically up to attempt limit. |
| `handover_limit` / `gate.closed` | Author hit session count or `250k` context ceiling. | Split oversized specs (`L` -> smaller `S`/`M` specs); check whether a clean candidate was recovered via `AEION_HANDOVER_CHECK` into review. |
