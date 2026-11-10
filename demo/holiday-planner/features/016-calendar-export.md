---
id: 016
sequence: 16
title: Take the plan into a calendar
goal: GOAL-016
area: sharing
size: S
phase: P4
parallel: false
write_paths: ["app/"]
depends_on: [005]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 016 — Take the plan into a calendar

## Intent

The itinerary exports to any calendar application. Success measure: The exported file imports with one event per activity.

Canonical source: `knowledge/spec/spec.json` GOAL-016 (spec `0a90103d634c`), requirements REQ-030.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Export an .ics file, one VEVENT per activity in floating local time (DEC-004), escaped and folded per RFC 5545.

**Requirements:**

- REQ-030 (should, risk medium): When a traveler exports a trip, the planner shall produce an iCalendar file with one event per activity, escaping text as RFC 5545 requires.

**Decisions:**

- DEC-004 Which time do exported calendar events use? -> floating local time at the destination

## Outputs

- COMP-006 Exports and search: Builds iCalendar files, backups and search results.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-044 (unit, normal) verifies REQ-030: A trip with three activities exports a VCALENDAR with three VEVENTs at floating local times.
- [ ] TEST-045 (unit, refusal) verifies REQ-030: Commas, semicolons, backslashes and line breaks in titles are escaped; long lines are folded at 75 octets.

## Out of scope

- Calendar subscriptions over the network.
