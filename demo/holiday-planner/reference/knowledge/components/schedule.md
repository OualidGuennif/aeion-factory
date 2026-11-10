---
type: Component
title: "Day schedule"
description: "One day's activities: validated times, ordered by start minute, never overlapping."
status: draft
spec_ids: [REQ-008, REQ-009, REQ-010, CON-002, COMP-002]
sources:
  - resource: ../../app/domain/schedule.py
    title: "Schedule.add"
  - resource: ../../app/tests/test_schedule.py
    title: "ScheduleTests"
---

# Day schedule

## Intent
Place activities on one day so the day never double-books a moment (REQ-010), keeping them in time
order (REQ-008) and refusing impossible times (REQ-009).

## Data sources
| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| The day's stored activities | id, start and end minute | Trip store | read inside the write transaction |

## Inputs
`Schedule.add(activity_id, title, start_minute, duration)`: title non-empty; start minute an integer
0-1439; duration a positive integer; the end may reach 1440 (midnight) and no further.

## Outputs
The new `Activity`. Refusals: `Refused(field, reason)` with `title/required`,
`start_minute/out_of_range`, `duration/not_positive`, `duration/past_midnight`; `Overlap` (field
`start_minute`, reason `overlap`) when CON-002 is false.

## Invariants
1. No two activities of the day overlap; touching ends are allowed (CON-001):
   `test_overlap_refused`, `test_back_to_back_accepted`.
2. A refused request leaves the day unchanged: `test_invalid_times_refused`, `test_overlap_refused`.
3. Activities stay ordered by start minute: `test_activities_ordered_by_start`.

## Determinism
deterministic: a pure function of the day and the request.

## Acceptance checks
```bash
python3 app/tests/test_schedule.py
tools/axiom/axiom evidence run --ids TEST-012,TEST-013,TEST-014,TEST-015
```

## Out of scope
- The write transaction that serializes concurrent requests (the store, TEST-016).
- Moving an activity: the same check, in round 03.
