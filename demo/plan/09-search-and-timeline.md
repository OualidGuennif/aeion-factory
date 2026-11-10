# Round 09: search and day timeline

- **017 Find anything quickly**: [`docs/features/017-search.md`](../holiday-planner/features/017-search.md) · GOAL-017 · REQ-031, REQ-032
- **018 See a day at a glance**: [`docs/features/018-day-timeline.md`](../holiday-planner/features/018-day-timeline.md) · GOAL-018 · REQ-033, REQ-034

## Focus

The interface round: make it beautiful and calm. A day is a vertical time grid (one row per 30 minutes), activities as cards sized by duration, one colour per category, readable in light and dark mode, everything reachable by keyboard with a visible focus. No framework: semantic HTML, one CSS file, a little vanilla JavaScript. REQ-034 also needs the manual review TEST-049: write its notes in `app/tests/manual/accessibility.md`.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-031,REQ-032,REQ-033,REQ-034
tools/axiom/axiom evidence run --ids TEST-046,TEST-047,TEST-048,TEST-049,TEST-050
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
open http://localhost:8000 and take screenshots for the journal
```

Done when the 5 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
