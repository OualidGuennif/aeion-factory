# Round 04: budget and expenses and over budget alert

- **007 Know what the trip costs**: [`docs/features/007-budget-and-expenses.md`](../holiday-planner/features/007-budget-and-expenses.md) · GOAL-007 · REQ-011, REQ-012, REQ-013
- **008 Spot overspending early**: [`docs/features/008-over-budget-alert.md`](../holiday-planner/features/008-over-budget-alert.md) · GOAL-008 · REQ-014

## Focus

Integer cents everywhere (DEC-005); no float ever touches money. CON-003 is soft: an over-budget expense is kept and flagged, never refused.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-011,REQ-012,REQ-013,REQ-014
tools/axiom/axiom evidence run --ids TEST-017,TEST-018,TEST-019
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom query node CON-003
```

Done when the 3 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
