# Round 01 — Scaffold

Plan: add app/deno.json, Fresh main/server/Vite/client modules, one API catch-all, version module, health tests and placeholder home. No storage, filters or Docker. Validate red tests, formatting, lint, types, tests, production build and HTTP smoke.

Fresh 2.3.3 and plugin 1.1.2 were verified against JSR metadata. Latest Vite 8.3.5 / Preact 11.1.0 exceed Fresh's declared major ranges: use latest compatible stable Vite 7.3.7 / Preact 10.29.8. Hono 4.13.14, std/assert 1.0.19, std/ulid 1.0.0. Exact pins and lockfile retained.

Implementation: separate Hono module and version; one Fresh catch-all; programmatic document wrapper. Tests failed before implementation (missing module); build and type check passed. HTTP smoke also exposed nested document tags from precompiled HTML; jsxPrecompileSkipElements fixes the wrapper recognition, rechecked with round 02 HTTP.

Evidence: evidence/01-red-network.txt, 01-quality-wrapper.txt, 01-build-wrapper.txt, 01-smoke-wrapper.txt, 01-factory-final.txt, and 02-smoke.txt for the corrected single HTML document.

Result:          done
Tests:           3 passed, 0 failed; build and HTTP smoke PASS
Factory checks:  knowledge-check, doc-links, repo-health: PASS
Guard refusals:  0; sandbox DNS/listen restrictions resolved through approved escalation
Human help:      0 direct actions; sandbox approvals requested by tooling
Feedback:        FB-001 seen
Elapsed:         12 minutes approximate, overlapped setup and round 02
