# Round 05: fair splits and packing list

- **009 Settle who owes whom**: [`docs/features/009-fair-splits.md`](../holiday-planner/features/009-fair-splits.md) · GOAL-009 · REQ-015, REQ-016, REQ-017
- **010 Pack without forgetting**: [`docs/features/010-packing-list.md`](../holiday-planner/features/010-packing-list.md) · GOAL-010 · REQ-018, REQ-019

## Focus

CON-004 is a hard **project** rule: every packet carries it. TEST-022 is a seeded property test (1000 cases, fixed seed, recorded in the test).

## Commands

```bash
tools/axiom/axiom packet --ids REQ-015,REQ-016,REQ-017,REQ-018,REQ-019
tools/axiom/axiom evidence run --ids TEST-020,TEST-021,TEST-022,TEST-023,TEST-024,TEST-025
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom packet --ids REQ-015
```

Done when the 6 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
