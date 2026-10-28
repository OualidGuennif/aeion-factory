---
type: Component
title: "Idea Board API"
description: "The Hono app mounted under /api in the Fresh server: health, and the JSON contract every /api response follows."
status: draft
generated:
  by: aeion-factory/1.3
  at: 2026-10-28
sources:
  - id: api
    resource: ../../app/api/app.ts
    title: "Hono app factory"
  - id: mount
    resource: "../../app/routes/api/[...path].ts"
    title: "Fresh catch-all route handing /api/* to Hono"
  - id: serve
    resource: ../../app/serve.ts
    title: "Production entry: PORT-aware server"
  - id: version
    resource: ../../app/version.ts
    title: "The app version"
---

# Idea Board API

## Intent
Serve every `/api/*` request from one Hono app, so the API is a plain module that can be tested without a server and
without Fresh. It serves the board's data contract to the page islands and to operators.

## Data sources
| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| `app/version.ts` | the app version | this app | build time |

## Inputs
- Any HTTP request whose path starts with `/api/`, handed over unchanged by `app/routes/api/[...path].ts`.

## Outputs
| Request | Status | Body |
| --- | --- | --- |
| `GET /api/health` | 200 | `{"status":"ok","version":"<version>"}` |
| any other method on `/api/health` | 405 | `{"error":"method_not_allowed"}` |
| unknown `/api/*` path | 404 | `{"error":"not_found"}` |
| an unexpected exception | 500 | `{"error":"internal"}` (no stack, no message) |

Every response has `content-type: application/json`.

## Invariants
1. Every `/api/*` response is JSON, errors included. Test: `app/api/app_test.ts` "unknown route is a JSON 404", "wrong method is a JSON 405".
2. `app/api/app.ts` imports nothing from Fresh. Test: `app/api/app_test.ts` "the API module does not import Fresh".
3. The catch-all route only forwards: no API logic in it. Checked by review; the route is a single `fetch` call.
4. An exception never leaks its message. Test: `app/api/app_test.ts` "an exception is a bare JSON 500".

## Determinism
deterministic: plain code, no model in the loop.

## Acceptance checks
```bash
cd app && deno test -A api/
deno task build && deno task start   # then curl -s localhost:8000/api/health
```

## Out of scope
- Authentication.
- Rate limiting.
- CORS: the API is same-origin only.
