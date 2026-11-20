---
id: 006
sequence: 6
title: "CSRF protection on every mutation"
area: foundation
size: S
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [005]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 006 — CSRF protection on every mutation

## Intent

Protect every cookie-authenticated mutation with a session-bound CSRF token and expose an authenticated `/api/auth/csrf` bootstrap endpoint.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Add the authenticated `GET /api/auth/csrf` bootstrap endpoint on `AuthResource`.
2. Verify constant-time header-only `CsrfGuard` enforcement across cookie-authenticated `POST` and `PUT` mutations.
3. Test unauthenticated/revoked `GET /api/auth/csrf` (401) and missing, URL-only, foreign, and valid `X-CSRF-Token` headers.

**Scope:**

- Provide an authenticated `GET /api/auth/csrf` bootstrap endpoint on `AuthResource` that authenticates the presented `agora_session` cookie via `AuthService.authenticate` (answering `401 {"error": "unauthorized"}` without a cookie, with an invalid/tampered cookie, or for an expired/revoked/disabled session, `503 {"error": "database_disabled"}` on a database-less boot, and `200 {"csrf": "..."}` matching the login payload `"csrf"` for a live session).
- Enforce `CsrfGuard` constant-time `X-CSRF-Token` header verification (`403 {"error": "csrf_invalid"}`) before routing any cookie-authenticated mutation (`POST`/`PUT`/`DELETE` under `/api/*`, including `POST /api/auth/logout`, `POST /api/auth/logout-all`, `POST /api/auth/accounts/{username}/disable`, `POST /api/threads`, `PUT /api/settings/{name}`, and cookie-bearing `POST /api/auth/login`); credential-exchange routes without a session cookie (`POST /api/auth/register`, cookie-less `POST /api/auth/login`) and `GET`/`HEAD`/`OPTIONS` requests stay callable without `X-CSRF-Token`.
- Never accept CSRF tokens from URL query parameters (`?csrf=...` or `?X-CSRF-Token=...` without a valid `X-CSRF-Token` header still answers `403 {"error": "csrf_invalid"}`).

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

CSRF tokens stay session-bound, are compared in constant time via `SessionSecret.csrfMatches`, and are read from the `X-CSRF-Token` header only (never from URL query parameters). `GET /api/auth/csrf` verifies live session state before returning a token.

This invariant and the acceptance cases belong to planned protected check `agora-006`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] `GET /api/auth/csrf` answers `401 {"error": "unauthorized"}` without a cookie, with a forged cookie, or after `POST /api/auth/logout` / `POST /api/auth/logout-all`, and answers `200 {"csrf": "<token>"}` (matching the login `"csrf"` field and usable in `X-CSRF-Token`) for an active session.
- [ ] Every cookie-authenticated `POST` or `PUT` mutation under `/api/*` without `X-CSRF-Token`, with a token from another session, or with the token supplied only in the URL query string answers `403 {"error": "csrf_invalid"}` and changes nothing.
- [ ] `GET` requests and cookie-less credential-exchange calls (`POST /api/auth/register`, cookie-less `POST /api/auth/login`) succeed without `X-CSRF-Token`.

**Test scenario:** Verify `GET /api/auth/csrf` returns 401 unauthenticated or after logout and returns 200 with the active session CSRF token when authenticated; exercise cookie-bearing `POST`/`PUT` mutations without a header, with a URL query token only, with another session token (all 403), and with the valid `X-CSRF-Token` header.

## Out of scope

- Third-party browser callers, permissive credentialed CORS, or persisting session credentials/CSRF tokens in localStorage.
- React/browser UI files in `demo/forum-web/` (added in 014) or internal agent token/broker endpoints (added in 053).
