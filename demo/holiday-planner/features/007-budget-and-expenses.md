---
id: 007
sequence: 7
title: Know what the trip costs
goal: GOAL-007
area: money
size: M
phase: P2
parallel: false
write_paths: ["app/"]
depends_on: [001]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 007 — Know what the trip costs

## Intent

Expenses add up to a visible total, in whole cents. Success measure: The total equals the sum of recorded expenses.

Canonical source: `knowledge/spec/spec.json` GOAL-007 (spec `0a90103d634c`), requirements REQ-011, REQ-012, REQ-013.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Record expenses in integer cents of the trip currency (DEC-005).
2. Show the total and, with a budget, the remaining cents.

**Requirements:**

- REQ-011 (must, risk medium): When a traveler records an expense with an amount, a payer and a category, the planner shall add it to the trip's total in whole cents.
- REQ-012 (should, risk low): While a trip has a budget, the planner shall show the remaining budget in cents.
- REQ-013 (must, risk medium): If an expense amount is not a positive number of cents, then the planner shall refuse the expense with the field amount_cents.

**Terms:**

- TERM-005 Cents: An integer number of the trip currency's hundredths; one currency per trip. Unit: cent.

**Decisions:**

- DEC-005 How is money stored? -> one currency per trip, integer cents

## Outputs

- COMP-001 Trip store: Persists trips, days, activities, expenses and bookings in one SQLite file, each change in one transaction.
- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- COMP-003 HTTP API and server: Serves the JSON API, the pages and the health check; maps refusals to stable status codes.
- Refusal (REQ-013): refuse the expense with the field amount_cents when an expense amount is not a positive number of cents.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-017 (unit, normal) verifies REQ-011, REQ-012: Expenses of 400.00 and 300.00 against a 1000.00 budget give a total of 70000 and 30000 cents remaining.
- [ ] TEST-018 (unit, refusal) verifies REQ-013: Amounts 0 and -5 are refused with field amount_cents; the total is unchanged.

## Out of scope

- Currency conversion.
- Receipts and photos.
