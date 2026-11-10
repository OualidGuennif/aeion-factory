# Round 03: activities and no overlaps

- **005 Plan activities in each day**: [`docs/features/005-activities.md`](../holiday-planner/features/005-activities.md) · GOAL-005 · REQ-008, REQ-009
- **006 Never double-book a moment**: [`docs/features/006-no-overlaps.md`](../holiday-planner/features/006-no-overlaps.md) · GOAL-006 · REQ-010

## Focus

The hard part of the product. CON-002 is checked inside one `BEGIN IMMEDIATE` transaction, and TEST-016 must force the race with a barrier (two threads released together), never with a sleep. Compare your code with the reference slice in the factory's `demo/holiday-planner/reference/` only after your tests pass.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-008,REQ-009,REQ-010
tools/axiom/axiom evidence run --ids TEST-012,TEST-013,TEST-014,TEST-015,TEST-016
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom query requirement REQ-010
```

Done when the 5 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
