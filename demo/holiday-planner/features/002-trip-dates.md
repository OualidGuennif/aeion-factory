---
id: 002
sequence: 2
title: Trip dates are always coherent
goal: GOAL-002
area: core
size: S
phase: P1
parallel: false
write_paths: ["app/"]
depends_on: [001]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 002 — Trip dates are always coherent

## Intent

A trip's dates never contradict themselves or exceed the agreed length. Success measure: No stored trip ends before it starts or lasts more than 60 days.

Canonical source: `knowledge/spec/spec.json` GOAL-002 (spec `0a90103d634c`), requirements REQ-003.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Validate start and end dates and the 60-day limit (DEC-001) in the domain layer.
2. Expose date changes through the API with stable 400 answers.

**Requirements:**

- REQ-003 (must, risk high): If a trip would end before it starts or last more than 60 days, then the planner shall refuse the dates without changing the trip.

**Decisions:**

- DEC-001 How long may one trip last? -> 60 days

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-003): refuse the dates without changing the trip when a trip would end before it starts or last more than 60 days.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-003 (unit, refusal) verifies REQ-003: An end before the start and a 61-day trip are refused; the stored trip is unchanged.
- [ ] TEST-004 (unit, normal) verifies REQ-003: A trip of exactly 60 days is accepted and has 60 days.
- [ ] TEST-005 (integration, refusal) verifies REQ-003: PUT with an end before the start answers 400 with field end_date; a GET returns the old dates.

## Out of scope

- Time zones: dates are calendar dates at the destination.
