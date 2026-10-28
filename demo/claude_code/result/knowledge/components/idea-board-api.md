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
  - id: filters
    resource: ../../app/domain/filters.ts
    title: "Tag and text filter parsing"
  - id: store
    resource: ../../app/store/ideas.ts
    title: "Ideas store on Deno KV"
  - id: kv
    resource: ../../app/store/kv.ts
    title: "Opening Deno KV from KV_PATH"
  - id: shared
    resource: ../../app/store/shared.ts
    title: "The one store the API and the page share"
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
| Deno KV (`KV_PATH`, default `./data/ideas.sqlite3`; `:memory:` in tests) | ideas under `["ideas", id]`; the votes index `["ideas_by_votes", votes, id] → id`; the tag index `["ideas_by_tag", tag, id] → id` | this app | live |

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
- `GET /api/ideas?limit=n&sort=s&tag=t&q=text`: `n` an integer 1–50, default 20; `s` is `recent` (default) or `votes`;
  filters parsed by `parseFilters` in `app/domain/filters.ts`, combined with AND, keeping the sort:

  | Parameter | Rule | Reason code |
  | --- | --- | --- |
  | `tag` | optional, `^[a-z0-9-]{1,20}$` | `bad_tag` |
  | `q` | optional, trimmed (empty reads as absent), at most 50 characters; a case-insensitive literal substring of the title or the description | `too_long` |

  A tag filter reads the tag index, never every idea. Filtered candidates are bounded to the **500 newest** ideas
  (with that tag, when a tag is given); the sort then orders those candidates. This is a stated bound, not a
  full-text engine.
- `POST /api/ideas/:id/vote`: no body.
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
| `GET /api/ideas?sort=votes` | 200 | most votes first; ties, newest first |
| `GET /api/ideas?sort=` anything else | 400 | field `sort`, reason `out_of_range` |
| `GET /api/ideas?tag=ui&q=dark` | 200 | the same shape, only ideas tagged `ui` whose title or description contains `dark` |
| `GET /api/ideas?tag=Bad_Tag` | 400 | field `tag`, reason `bad_tag` |
| `GET /api/ideas?q=` over 50 characters | 400 | field `q`, reason `too_long` |
| `POST /api/ideas/:id/vote` | 200 | `{"idea": Idea}`, `votes` one more |
| `POST /api/ideas/:id/vote`, unknown id | 404 | `{"error":"not_found"}`, nothing written |
| `POST /api/ideas/:id/vote`, still conflicting after 10 attempts | 503 | `{"error":"busy"}` |
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
10. N concurrent votes on one idea add exactly N. A vote is an optimistic transaction (`check` on the idea's
    versionstamp) retried at most 10 times with a jittered backoff. Test: `app/store/votes_test.ts` "25 concurrent votes are all counted".
11. The idea and its index key move in one atomic commit, so the index holds exactly one key per idea. Test:
    `app/store/votes_test.ts` "the index keeps one key per idea".
12. A vote for an unknown id writes nothing. Test: `app/store/votes_test.ts` "an unknown id writes nothing".
13. Creating an idea writes its tag keys in the same atomic commit. Test: `app/store/search_test.ts` "create indexes every tag".
14. A tag filter returns exactly the ideas with that tag. Test: `app/store/search_test.ts` "a tag filter is exact" (3 tags, 6 ideas).
15. `q` ignores case and is never a regular expression. Test: `app/store/search_test.ts` "regex characters are literal".
16. Filtering looks at most at the 500 newest candidates. Test: `app/store/search_test.ts` "search stops at the 500 newest".

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
- One vote per person, un-voting, rate limiting of votes.
- Full-text ranking, fuzzy matching, tag renaming, tag counts.
