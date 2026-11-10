# Round 07: bookings and trip lifecycle

- **013 Keep bookings together**: [`docs/features/013-bookings.md`](../holiday-planner/features/013-bookings.md) · GOAL-013 · REQ-023, REQ-024, REQ-025
- **014 Know where each trip stands**: [`docs/features/014-trip-lifecycle.md`](../holiday-planner/features/014-trip-lifecycle.md) · GOAL-014 · REQ-026

## Focus

Masking happens before data leaves the server (TEST-035 reads raw API bodies). The lifecycle comes from MODEL-001: generate the allowed-transition table from the spec's model, not from memory. DEC-006 stays open: do not make completed trips read-only.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-023,REQ-024,REQ-025,REQ-026
tools/axiom/axiom evidence run --ids TEST-031,TEST-032,TEST-033,TEST-034,TEST-035,TEST-036,TEST-037,TEST-038
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
tools/axiom/axiom query node MODEL-001
```

Done when the 8 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
