---
id: 006
sequence: 6
title: Never double-book a moment
goal: GOAL-006
area: planning
size: M
phase: P2
parallel: false
write_paths: ["app/"]
depends_on: [005]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 006 — Never double-book a moment

## Intent

Two activities of the same day never overlap. Success measure: No stored day holds overlapping activities, even under concurrent requests.

Canonical source: `knowledge/spec/spec.json` GOAL-006 (spec `0a90103d634c`), requirements REQ-010.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`
- ENV-001: One day's schedule and a requested slot

## Inputs

**Delivery steps:**

1. Check CON-002 inside one BEGIN IMMEDIATE transaction per change.
2. Prove two concurrent overlapping requests admit exactly one (barrier test).

**Requirements:**

- REQ-010 (must, risk high): If a new or moved activity would overlap another activity of the same day, then the planner shall refuse it without changing the day.

**Terms:**

- TERM-003 Activity: A titled item on one day, from a start minute for a positive duration, ending no later than midnight.
- TERM-004 Minute of day: An integer from 0 (00:00) to 1440 (midnight at the end of the day), local to the destination. Unit: minute.

## Outputs

- COMP-001 Trip store: Persists trips, days, activities, expenses and bookings in one SQLite file, each change in one transaction.
- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-010): refuse it without changing the day when a new or moved activity would overlap another activity of the same day.

## Invariants

- CON-001 No two activities of a day overlap (invariant, hard): BCIR predicate in ENV-001; checked by TEST-014, TEST-015, TEST-016.
- CON-002 A requested slot fits the day (admission_guard, hard): BCIR predicate in ENV-001; checked by TEST-014, TEST-015.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-014 (unit, refusal) verifies REQ-010: Adding 09:30-10:30 to a day holding 09:00-10:00 raises Overlap and the day still holds one activity.
- [ ] TEST-015 (unit, normal) verifies REQ-010: Activities 09:00-10:00 and 10:00-11:00 are both accepted: touching ends do not overlap.
- [ ] TEST-016 (integration, refusal) verifies REQ-010: Two simultaneous requests for overlapping slots, released together by a barrier, admit exactly one; the stored day passes CON-001.

**Test scenario:** SCN-001 (witness) on add activity: The new activity is placed after lunch; touching ends are not overlaps. SCN-002 (counterexample) on audit day: The day is invalid: museum and lunch overlap by 20 minutes. SCN-003 (witness) on add activity: The request is refused and the day keeps only the museum.

## Out of scope

- Suggesting a free slot.
