---
id: 009
sequence: 9
title: Settle who owes whom
goal: GOAL-009
area: money
size: L
phase: P3
parallel: false
write_paths: ["app/"]
depends_on: [003, 007]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 009 — Settle who owes whom

## Intent

Shared expenses are split fairly and balances settle to zero. Success measure: Shares always add up to the expense, to the cent.

Canonical source: `knowledge/spec/spec.json` GOAL-009 (spec `0a90103d634c`), requirements REQ-015, REQ-016, REQ-017.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`
- ENV-003: One expense and its shares

## Inputs

**Delivery steps:**

1. Split an expense in whole cents, the payer taking the remainder (DEC-002, CON-004).
2. Compute balances that add up to zero and expose them through the API.
3. Add a seeded property test over 1000 random splits.

**Requirements:**

- REQ-015 (must, risk high): When an expense is split among travelers, the planner shall assign each share in whole cents so the shares add up exactly to the amount, remaining cents going to the payer.
- REQ-016 (must, risk medium): The planner shall compute each traveler's balance as paid minus owed, in cents.
- REQ-017 (must, risk high): If an expense is split among no traveler or among someone who is not on the trip, then the planner shall refuse the split and keep the expense unsplit.

**Terms:**

- TERM-005 Cents: An integer number of the trip currency's hundredths; one currency per trip. Unit: cent.
- TERM-007 Balance: What a traveler paid minus what they owe, in cents; balances of a trip add up to zero. Unit: cent.

**Decisions:**

- DEC-002 Who receives the cents left over when an expense does not divide evenly? -> the payer

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-017): refuse the split and keep the expense unsplit when an expense is split among no traveler or among someone who is not on the trip.

## Invariants

- CON-004 Shares add up to the expense (invariant, hard): BCIR predicate in ENV-003; checked by TEST-020, TEST-022.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-020 (unit, normal) verifies REQ-015, REQ-017: 1000 cents among the payer, Ana and Ben give 334, 333 and 333; the payer gets the remainder.
- [ ] TEST-021 (unit, refusal) verifies REQ-017: A split among nobody, or including someone not on the trip, is refused; the expense stays unsplit.
- [ ] TEST-022 (property, refusal) verifies REQ-015: For 1000 seeded random amounts and traveler counts, shares always add up to the amount and differ by at most one cent.
- [ ] TEST-023 (integration, normal) verifies REQ-015, REQ-016: After three split expenses, the balances endpoint returns paid minus owed per traveler and they add up to zero.
- [ ] TEST-024 (integration, refusal) verifies REQ-017: Splitting with a traveler not on the trip answers 400 and the expense stays unsplit.

**Test scenario:** SCN-006 (witness) on split expense: The payer's share takes the remaining cent; shares add up to 1000. SCN-007 (counterexample) on split expense: Invalid: one cent is lost, so balances would not settle.

## Out of scope

- Settling payments between travelers.
