# Round 08: safe sharing and calendar export

- **015 Share the plan safely**: [`docs/features/015-safe-sharing.md`](../holiday-planner/features/015-safe-sharing.md) · GOAL-015 · REQ-027, REQ-028, REQ-029
- **016 Take the plan into a calendar**: [`docs/features/016-calendar-export.md`](../holiday-planner/features/016-calendar-export.md) · GOAL-016 · REQ-030

## Focus

RISK-001 and CTRL-001 govern this round: `secrets.token_urlsafe(16)` or more, revocation, and byte-identical 404 bodies for unknown and revoked tokens. The calendar uses floating local times (DEC-004) and RFC 5545 escaping and folding.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-027,REQ-028,REQ-029,REQ-030
tools/axiom/axiom evidence run --ids TEST-039,TEST-040,TEST-041,TEST-042,TEST-043,TEST-044,TEST-045
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom packet --ids REQ-027,REQ-028,REQ-029
```

Done when the 7 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
