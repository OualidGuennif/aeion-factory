---
id: 005
sequence: 5
title: "Sessions with signed cookies"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [004]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 005 — Sessions with signed cookies

## Intent

Issue short-lived HttpOnly sessions whose identifier is rotated on login and privilege change, so a stolen cookie has a bounded life and a visible history.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Add opaque server-side sessions and the protected cookie contract.
2. Implement login rotation, expiry and logout without browser token storage.
3. Test old-cookie refusal, expiry and logout-everywhere.

**Scope:**

- Signed `agora_session` cookie keeping the existing `AuthResource`/`AuthResourceTest` contract: `HttpOnly`, `Path=/`, `SameSite=Strict`, and `Secure` only over HTTPS (omitted over plain loopback HTTP).
- Server-side session rows with expiry (keeping `SESSION_SECONDS=900` defaults intact), rotating and revoking any valid incoming `agora_session` cookie presented on `POST /api/auth/login` (supplying that session's `X-CSRF-Token` per `CsrfGuard`) without revoking unrelated sessions, plus CSRF-protected `POST /api/auth/logout-all` (`401` unauthenticated, `403` without `X-CSRF-Token`) revoking all sessions for the current account.
- Configurable idle timeout and absolute lifetime enforced in JUnit/service checks via `ForumClock`, plus optional secondary env verification keys preserving `SessionSecret` refusal codes and `<token>.<hmac>` signing.

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Primary and verification signing keys come from environment configuration, are never logged, and rotate without invalidating every live session at once.

This invariant and the acceptance cases belong to planned protected check `agora-005`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] The `Set-Cookie` on `POST /api/auth/login` emits `HttpOnly`, `Path=/`, and `SameSite=Strict`; `POST /api/auth/logout` and CSRF-protected `POST /api/auth/logout-all` invalidate active sessions (`GET /api/auth/me` returns 401; `logout-all` returns 401 without a session and 403 without `X-CSRF-Token`).
- [ ] Calling `POST /api/auth/login` with an existing valid `agora_session` cookie and its matching `X-CSRF-Token` header issues a rotated cookie with its new CSRF token and revokes only that presented cookie (reusing it fails with 401), leaving separate unpresented sessions valid until `POST /api/auth/logout-all`.
- [ ] Idle and absolute expiry answer empty/401 without redirect loops in JUnit/service checks with frozen `ForumClock`, and rotated verification keys keep authenticating prior sessions without breaking `SessionSecretTest`.

**Test scenario:** Open two independent logins without sharing the first cookie, verify `POST /api/auth/logout-all` (with `X-CSRF-Token`) revokes both while logging in with an active cookie and its `X-CSRF-Token` rotates and invalidates only that old cookie; verify idle/absolute expiry in JUnit with frozen `ForumClock` and verification key rotation.

## Out of scope

- OAuth, OIDC or a third-party identity provider.
- Remember-me cookies beyond the absolute lifetime, React/browser UI (added in 014), or global frozen clocks across live HTTP requests.
