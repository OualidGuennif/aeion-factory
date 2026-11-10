# Round 06: day notes and places

- **011 Keep notes for each day**: [`docs/features/011-day-notes.md`](../holiday-planner/features/011-day-notes.md) · GOAL-011 · REQ-020
- **012 Find the places of the trip**: [`docs/features/012-places.md`](../holiday-planner/features/012-places.md) · GOAL-012 · REQ-021, REQ-022

## Focus

Escaping is a requirement (REQ-020), not a style: one escaping function used by every page, and an e2e test that reads the served HTML. Coordinates are integer microdegrees; map links are plain OpenStreetMap URLs, no API call.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-020,REQ-021,REQ-022
tools/axiom/axiom evidence run --ids TEST-026,TEST-027,TEST-028,TEST-029,TEST-030
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom query tests app/pages.py
```

Done when the 5 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
