# Round 01: trip workspace and trip dates

- **001 Keep every trip in one workspace**: [`docs/features/001-trip-workspace.md`](../holiday-planner/features/001-trip-workspace.md) · GOAL-001 · REQ-001, REQ-002
- **002 Trip dates are always coherent**: [`docs/features/002-trip-dates.md`](../holiday-planner/features/002-trip-dates.md) · GOAL-002 · REQ-003

## Focus

The skeleton: `app/server.py` on `http.server.ThreadingHTTPServer`, `app/store.py` owning the only SQLite connection (one transaction per change), and a first page. Settle the JSON error shape once: `{"error": "invalid", "field": ..., "reason": ...}`.

## Commands

```bash
tools/axiom/axiom packet --ids REQ-001,REQ-002,REQ-003
tools/axiom/axiom evidence run --ids TEST-001,TEST-002,TEST-003,TEST-004,TEST-005
tools/axiom/axiom docs && tools/axiom/axiom check
tools/axiom/axiom validate --phase implementation
curl -s -X POST localhost:8000/api/trips -d '{"name":"Lisbon","destination":"Lisbon","start_date":"2027-07-01","end_date":"2027-07-10"}'
```

Done when the 5 test cases above have current passing receipts, the factory checks pass, and the record block of [round 00](00-start.md) is filled.
