---
id: 004
sequence: 4
title: See the trip day by day
goal: GOAL-004
area: planning
size: M
phase: P1
parallel: false
write_paths: ["app/"]
depends_on: [002]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 004 — See the trip day by day

## Intent

The trip is laid out as one page per calendar day. Success measure: Days always match the trip's dates without losing planned activities.

Canonical source: `knowledge/spec/spec.json` GOAL-004 (spec `0a90103d634c`), requirements REQ-006, REQ-007.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Derive one day per calendar date when dates are set or changed.
2. Refuse shortening onto days that hold activities, naming them (409).

**Requirements:**

- REQ-006 (must, risk medium): When a trip's dates are set or changed, the planner shall list one day per calendar date from start to end, keeping existing day content.
- REQ-007 (must, risk high): If shortening the dates would remove a day that holds activities, then the planner shall refuse the change and name the affected days.

**Terms:**

- TERM-002 Day: One calendar date of a trip, from start to end inclusive.

## Outputs

- COMP-001 Trip store: Persists trips, days, activities, expenses and bookings in one SQLite file, each change in one transaction.
- Refusal (REQ-007): refuse the change and name the affected days when shortening the dates would remove a day that holds activities.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-008 (unit, normal) verifies REQ-006: A 3-day trip has 3 days; extending it to 5 keeps the content of the first 3.
- [ ] TEST-009 (unit, refusal) verifies REQ-007: Shortening a trip whose last day holds an activity is refused, naming that day; dates are unchanged.
- [ ] TEST-010 (unit, normal) verifies REQ-007: Shortening a trip whose removed days are empty succeeds and drops exactly those days.
- [ ] TEST-011 (integration, refusal) verifies REQ-007: The API answers 409 with the affected days and the stored trip keeps its dates and activities.

## Out of scope

- Moving activities automatically when dates change.
