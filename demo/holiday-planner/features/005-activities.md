---
id: 005
sequence: 5
title: Plan activities in each day
goal: GOAL-005
area: planning
size: M
phase: P2
parallel: false
write_paths: ["app/"]
depends_on: [004]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 005 — Plan activities in each day

## Intent

Travelers place activities at a time on a day. Success measure: Activities appear on their day in time order.

Canonical source: `knowledge/spec/spec.json` GOAL-005 (spec `0a90103d634c`), requirements REQ-008, REQ-009.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Add activities with title, start minute, duration and category.
2. Order them by start minute; refuse invalid times with their field.

**Requirements:**

- REQ-008 (must, risk medium): When a traveler adds an activity with a title, a day, a start minute and a duration, the planner shall place it on that day, ordered by start minute.
- REQ-009 (must, risk medium): If an activity's start minute is outside 0-1439, its duration is not positive or it ends after midnight, then the planner shall refuse the activity with the field and a reason code.

**Terms:**

- TERM-003 Activity: A titled item on one day, from a start minute for a positive duration, ending no later than midnight.
- TERM-004 Minute of day: An integer from 0 (00:00) to 1440 (midnight at the end of the day), local to the destination. Unit: minute.

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-009): refuse the activity with the field and a reason code when an activity's start minute is outside 0-1439, its duration is not positive or it ends after midnight.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-012 (unit, normal) verifies REQ-008: Activities added at 14:00 then 09:00 list as 09:00, 14:00.
- [ ] TEST-013 (unit, refusal) verifies REQ-009: Start 1440, duration 0 and an end after midnight are each refused with their field; the day is unchanged.

## Out of scope

- Recurring activities.
- Travel time between places.
