# Round 00 — Setup

Plan: qualify the existing plain-folder copy, use only codex/, run factory tests and hook fixtures, then implement rounds 01–07 in order. Owner authorized all rounds on 2026-10-28; this overrides the per-round pause. No push; commits still require sandbox approval.

Baseline: factory 1.4.0, prepared copy 578f4f3; parent branch develop, initially clean. Deno 2.9.8, Docker client 29.9.2. Graphify status: 1,209 nodes, 2,100 edges, 163 files, no unresolved spec links. The parent graph tool works with --root codex/workspace; no setup was run.

Hook fixture battery: 0 failures (10 PASS cases, 5 informational probes). This runs Claude hook payloads directly; it does not prove native Codex dispatch. Native project hooks are configured, but trust and dispatch in this session are unverified.

Factory tests: PASS, 734 passed and 2 skipped. Full replay output: evidence/00-factory-final.txt. Three factory checks passed after scaffold creation (evidence/01-factory-final.txt); this is not a pristine-copy baseline. No native hook activation is claimed.

Result:          done
Tests:           734 factory passed, 0 failed, 2 skipped; hook battery 0 failures
Factory checks:  knowledge-check, doc-links, repo-health: PASS (after scaffold)
Guard refusals:  0 native observed; expected fixture refusals are not native dispatch
Human help:      0 after approval to run all rounds
Feedback:        FB-001 new, inherited task state (same class as prior harness FB-003)
Elapsed:         14 minutes (approximate wall time, setup and scaffold investigations overlap)
