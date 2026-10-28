# Round 02 — Ideas API

Plan: pure ordered validation in domain/idea.ts, injected KV store (store/ideas.ts), lazy runtime KV opener, Hono create/list/get routes and tests. Keep the single Fresh catch-all. No votes, filters or Docker. Validate every refusal, size in bytes, no invalid writes, ULID newest ordering and HTTP smoke.

Tests were added before implementation and failed on absent domain/store modules. Added byte-counted request reading, ordered pure validation, monotonic ULIDs, injected KV and lazy process store. Default KV directory is created only on first runtime use. No store is opened at build time.

Evidence: evidence/02-red.txt, 02-quality.txt, 02-build.txt, 02-smoke.txt, 02-factory.txt. Graph queried rdeps/tests/spec for the store and domain before further changes.

Result:          done
Tests:           35 passed, 0 failed; build and HTTP smoke PASS
Factory checks:  knowledge-check, doc-links, repo-health: PASS
Guard refusals:  0
Human help:      0 direct actions; approved sandbox network/listen requests
Feedback:        FB-001 seen
Elapsed:         7 minutes approximate
