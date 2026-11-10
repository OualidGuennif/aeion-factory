---
id: 017
sequence: 17
title: Find anything quickly
goal: GOAL-017
area: planning
size: S
phase: P4
parallel: false
write_paths: ["app/"]
depends_on: [005]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 017 — Find anything quickly

## Intent

Search across trips, activities, places and notes. Success measure: A search returns every item containing the text.

Canonical source: `knowledge/spec/spec.json` GOAL-017 (spec `0a90103d634c`), requirements REQ-031, REQ-032.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Search trips, activities, places and notes case-insensitively; refuse terms under 2 or over 100 characters.

**Requirements:**

- REQ-031 (should, risk low): When a traveler searches with text, the planner shall return the trips, activities, places and notes whose text contains it, ignoring case.
- REQ-032 (must, risk low): If a search term is shorter than 2 or longer than 100 characters, then the planner shall refuse it with the field q and a reason code.

## Outputs

- COMP-003 HTTP API and server: Serves the JSON API, the pages and the health check; maps refusals to stable status codes.
- COMP-006 Exports and search: Builds iCalendar files, backups and search results.
- Refusal (REQ-032): refuse it with the field q and a reason code when a search term is shorter than 2 or longer than 100 characters.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-046 (unit, normal) verifies REQ-031: Searching 'louvre' returns the activity, the place and the note that contain Louvre.
- [ ] TEST-047 (unit, refusal) verifies REQ-032: Terms of 1 and 101 characters are refused with field q.

## Out of scope

- Fuzzy matching.
