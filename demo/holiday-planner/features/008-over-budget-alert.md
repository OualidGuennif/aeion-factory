---
id: 008
sequence: 8
title: Spot overspending early
goal: GOAL-008
area: money
size: S
phase: P2
parallel: false
write_paths: ["app/"]
depends_on: [007]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 008 — Spot overspending early

## Intent

A trip over its budget is flagged as soon as it happens. Success measure: Every over-budget trip shows the flag; no other trip does.

Canonical source: `knowledge/spec/spec.json` GOAL-008 (spec `0a90103d634c`), requirements REQ-014.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`
- ENV-002: A trip's budget and expenses

## Inputs

**Delivery steps:**

1. Flag a trip whose expenses exceed its budget, with the excess in cents (CON-003).

**Requirements:**

- REQ-014 (must, risk medium): If the recorded expenses exceed the trip budget, then the planner shall flag the trip as over budget without refusing the expense.

**Terms:**

- TERM-005 Cents: An integer number of the trip currency's hundredths; one currency per trip. Unit: cent.

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-014): flag the trip as over budget without refusing the expense when the recorded expenses exceed the trip budget.

## Invariants

- CON-003 Expenses stay within the budget (invariant, soft): BCIR predicate in ENV-002; checked by TEST-019.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-019 (unit, normal) verifies REQ-014: The flag is off within the budget and on, with the excess in cents, once expenses exceed it; no expense is refused.

**Test scenario:** SCN-004 (witness) on record expense: No over-budget flag; 30000 cents remain. SCN-005 (counterexample) on record expense: The expense is kept and the trip is flagged over budget by 20000 cents.

## Out of scope

- Refusing expenses: the budget is a guide, not a limit.
