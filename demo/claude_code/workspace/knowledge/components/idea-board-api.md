---
type: Component
title: "Idea Board API"
description: "The Hono app mounted under /api in the Fresh server: health, ideas on Deno KV, and the JSON contract every /api response follows."
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
  - id: domain
    resource: ../../app/domain/idea.ts
    title: "Idea type and validation"
  - id: store
    resource: ../../app/store/ideas.ts
    title: "Ideas store on Deno KV"
  - id: kv
    resource: ../../app/store/kv.ts
    title: "Opening Deno KV from KV_PATH"
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
| Deno KV (`KV_PATH`, default `./data/ideas.sqlite3`; `:memory:` in tests) | ideas under `["ideas", id]` | this app | live |

## Inputs
- Any HTTP request whose path starts with `/api/`, handed over unchanged by `app/routes/api/[...path].ts`.
- `POST /api/ideas`: a JSON object (`content-type: application/json`, at most 8 KiB), validated by
  `validateNewIdea` in `app/domain/idea.ts`, fields checked in this order:

  | Field | Rule | Reason codes |
  | --- | --- | --- |
  | (body) | a JSON object | `malformed_json`, `not_object` |
  | `title` | string, trimmed, 3–80 characters | `required`, `too_short`, `too_long` |
  | `description` | optional string, trimmed, at most 500, default `""` | `not_string`, `too_long` |
  | `tags` | optional array, 0–5 unique items matching `^[a-z0-9-]{1,20}$` | `not_array`, `too_many`, `bad_tag`, `duplicate` |
  | any other key | refused | `unknown_field` (field = that key) |
- `GET /api/ideas?limit=n`: `n` an integer 1–50, default 20.
- `GET /api/ideas/:id`.

**Idea.** `{ id: ULID, title, description, tags: string[], votes: number, createdAt: ISO 8601 }`.

## Outputs
| Request | Status | Body |
| --- | --- | --- |
| `GET /api/health` | 200 | `{"status":"ok","version":"<version>"}` |
| any other method on `/api/health` | 405 | `{"error":"method_not_allowed"}` |
| `POST /api/ideas` valid | 201 | `{"idea": Idea}`, `votes` 0 |
| `POST /api/ideas` invalid | 400 | `{"error":"invalid","field":"<name>","reason":"<code>"}`, the first failing field |
| `POST /api/ideas` without a JSON content type | 415 | `{"error":"unsupported_media_type"}` |
| `POST /api/ideas` body over 8 KiB | 413 | `{"error":"too_large"}` |
| `GET /api/ideas` | 200 | `{"ideas": Idea[], "count": n}`, newest first |
| `GET /api/ideas?limit=` 0, 51, `x`, `1.5` | 400 | field `limit`, reason `out_of_range` |
| `GET /api/ideas/:id` | 200 / 404 | `{"idea": Idea}` / `{"error":"not_found"}` |
| unknown `/api/*` path | 404 | `{"error":"not_found"}` |
| an unexpected exception | 500 | `{"error":"internal"}` (no stack, no message) |

Every response has `content-type: application/json`.

## Invariants
1. Every `/api/*` response is JSON, errors included. Test: `app/api/app_test.ts` "unknown route is a JSON 404", "wrong method is a JSON 405".
2. `app/api/app.ts` imports nothing from Fresh. Test: `app/api/app_test.ts` "the API module does not import Fresh".
3. The catch-all route only forwards: no API logic in it. Checked by review; the route is a single `fetch` call.
4. An exception never leaks its message. Test: `app/api/app_test.ts` "an exception is a bare JSON 500".
5. Validation is a pure function, tested without KV or HTTP. Test: `app/domain/idea_test.ts` (one test per reason code).
6. The store takes its `Deno.Kv` as a parameter. Test: `app/store/ideas_test.ts` runs on `Deno.openKv(":memory:")`.
7. An invalid request writes nothing. Test: `app/api/ideas_test.ts` "invalid writes nothing".
8. Ids are monotonic ULIDs, so key order is creation order, even within one millisecond. Test: `app/store/ideas_test.ts` "list is newest first".
9. KV opens lazily on the first request, never at build time. Checked: `deno task build` creates no `data/` folder.

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
- Editing or deleting ideas; pagination cursors.
