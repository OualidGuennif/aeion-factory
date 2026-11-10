---
id: 003
sequence: 3
title: Know who travels
goal: GOAL-003
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

# 003 — Know who travels

## Intent

Each trip lists its travelers and who organizes. Success measure: Every traveler appears once per trip with a role.

Canonical source: `knowledge/spec/spec.json` GOAL-003 (spec `0a90103d634c`), requirements REQ-004, REQ-005.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Add travelers with the organizer or companion role.
2. Refuse duplicate names within a trip.

**Requirements:**

- REQ-004 (must, risk medium): When an organizer adds a traveler to a trip, the planner shall store the traveler with the role organizer or companion.
- REQ-005 (must, risk medium): If a traveler's name already exists in the trip, then the planner shall refuse the duplicate and keep the existing traveler.

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-005): refuse the duplicate and keep the existing traveler when a traveler's name already exists in the trip.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-006 (unit, normal) verifies REQ-004: An organizer and a companion are stored with their roles; an unknown role is refused.
- [ ] TEST-007 (unit, refusal) verifies REQ-005: Adding Ana twice is refused with reason duplicate; the trip has one Ana.

## Out of scope

- Contact details and invitations.
