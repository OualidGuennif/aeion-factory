# Round 02: travelers and day by day

- **003 Know who travels**: [`docs/features/003-travelers.md`](../holiday-planner/features/003-travelers.md) · GOAL-003 · REQ-004, REQ-005
- **004 See the trip day by day**: [`docs/features/004-day-by-day.md`](../holiday-planner/features/004-day-by-day.md) · GOAL-004 · REQ-006, REQ-007

## Focus

Days are derived, not stored by hand: changing dates recomputes them. The refusal of REQ-007 must name the days that hold activities and leave the trip untouched.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-004,REQ-005,REQ-006,REQ-007
tools/axiom/axiom evidence run --ids TEST-006,TEST-007,TEST-008,TEST-009,TEST-010,TEST-011
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom packet --ids REQ-006,REQ-007
```

Done when the 6 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
