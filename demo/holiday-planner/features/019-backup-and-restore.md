---
id: 019
sequence: 19
title: Never lose a trip
goal: GOAL-019
area: operations
size: M
phase: P5
parallel: false
write_paths: ["app/"]
depends_on: [001]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 019 — Never lose a trip

## Intent

Backups export and import every trip safely. Success measure: A backup imports back to identical trips; a bad file changes nothing.

Canonical source: `knowledge/spec/spec.json` GOAL-019 (spec `0a90103d634c`), requirements REQ-035, REQ-036.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Export every trip as versioned JSON, all or nothing.
2. Import into the store in one transaction; refuse unknown versions and invalid files without change.

**Requirements:**

- REQ-035 (must, risk high): When an organizer exports a backup, the planner shall write every trip as JSON with a schema version, all or nothing.
- REQ-036 (must, risk high): If an imported backup has an unknown schema version or fails validation, then the planner shall refuse it without changing the stored trips.

## Outputs

- COMP-001 Trip store: Persists trips, days, activities, expenses and bookings in one SQLite file, each change in one transaction.
- COMP-006 Exports and search: Builds iCalendar files, backups and search results.
- Refusal (REQ-036): refuse it without changing the stored trips when an imported backup has an unknown schema version or fails validation.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-051 (unit, normal) verifies REQ-035: Exporting then importing into an empty store gives byte-identical trip records.
- [ ] TEST-052 (unit, refusal) verifies REQ-036: A backup with schema version 99 is refused with reason unsupported_version.
- [ ] TEST-053 (integration, refusal) verifies REQ-036: An import whose third trip is invalid answers 400 and the store keeps exactly its previous trips.
- [ ] TEST-054 (unit, refusal) verifies REQ-035: An export interrupted after the first trip leaves no partial backup file.
- [ ] TEST-055 (integration, normal) verifies REQ-035, REQ-036: GET /api/backup then POST it to a fresh store answers 200 and lists the same trips.

## Out of scope

- Cloud sync.
