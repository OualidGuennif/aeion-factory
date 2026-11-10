---
id: 013
sequence: 13
title: Keep bookings together
goal: GOAL-013
area: travel
size: M
phase: P3
parallel: false
write_paths: ["app/"]
depends_on: [002]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 013 — Keep bookings together

## Intent

Flights, stays and tickets attached to the trip, codes protected. Success measure: Bookings fit the trip's dates and codes are never fully shown.

Canonical source: `knowledge/spec/spec.json` GOAL-013 (spec `0a90103d634c`), requirements REQ-023, REQ-024, REQ-025.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Attach bookings inside the trip's dates.
2. Mask confirmation codes everywhere except their last four characters.

**Requirements:**

- REQ-023 (must, risk medium): When a traveler records a booking with a kind, dates and a confirmation code, the planner shall attach it to the trip.
- REQ-024 (must, risk high): The planner shall show a confirmation code masked except its last four characters.
- REQ-025 (must, risk medium): If a booking's dates fall outside the trip, then the planner shall refuse the booking with the field dates.

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- COMP-004 Web pages: Renders the trip, day timeline, shared view and forms, escaping every value.
- Refusal (REQ-025): refuse the booking with the field dates when a booking's dates fall outside the trip.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-031 (unit, normal) verifies REQ-023: A hotel booking inside the trip is attached and listed with its kind and dates.
- [ ] TEST-032 (unit, refusal) verifies REQ-025: A booking starting the day before the trip is refused with field dates.
- [ ] TEST-033 (unit, normal) verifies REQ-024: Code ABC12345 displays as ****2345.
- [ ] TEST-034 (unit, refusal) verifies REQ-024: A code of four characters or fewer displays as **** only.
- [ ] TEST-035 (integration, refusal) verifies REQ-024: No API response body for a trip with bookings contains a full confirmation code.

## Out of scope

- Importing booking emails.
