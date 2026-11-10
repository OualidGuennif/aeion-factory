---
id: 014
sequence: 14
title: Know where each trip stands
goal: GOAL-014
area: core
size: S
phase: P3
parallel: false
write_paths: ["app/"]
depends_on: [001]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 014 — Know where each trip stands

## Intent

A trip moves through draft, planned, booked, completed or cancelled. Success measure: Only declared status changes ever happen.

Canonical source: `knowledge/spec/spec.json` GOAL-014 (spec `0a90103d634c`), requirements REQ-026.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Implement MODEL-001's transitions; refuse any other change with 409.

**Requirements:**

- REQ-026 (must, risk high): If a requested status change is not a declared transition, then the planner shall refuse it and keep the current status.

**Decisions:**

- DEC-006 Should a completed trip become read-only? -> open

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-026): refuse it and keep the current status when a requested status change is not a declared transition.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-036 (unit, refusal) verifies REQ-026: completed -> draft and cancelled -> planned are refused; the status is unchanged.
- [ ] TEST-037 (unit, normal) verifies REQ-026: draft -> planned -> booked -> completed succeeds step by step.
- [ ] TEST-038 (integration, refusal) verifies REQ-026: POST status draft on a completed trip answers 409 and the trip stays completed.

## Out of scope

- Read-only completed trips: DEC-006 is still open.
