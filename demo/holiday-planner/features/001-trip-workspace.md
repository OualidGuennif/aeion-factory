---
id: 001
sequence: 1
title: Keep every trip in one workspace
goal: GOAL-001
area: core
size: M
phase: P1
parallel: false
write_paths: ["app/"]
depends_on: []
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 001 — Keep every trip in one workspace

## Intent

A family creates trips and finds them again in one place. Success measure: A created trip is listed and opens with everything entered.

Canonical source: `knowledge/spec/spec.json` GOAL-001 (spec `0a90103d634c`), requirements REQ-001, REQ-002.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Create app/ with the standard-library server, the SQLite store and a trips table.
2. Add create, read and list for trips, newest first, with the name rules.
3. Serve a trips page that lists and creates trips.

**Requirements:**

- REQ-001 (must, risk medium): When a traveler creates a trip with a name, a destination and dates, the planner shall store the trip and return its identifier, newest trips listed first.
- REQ-002 (must, risk medium): If a trip name is empty or longer than 80 characters, then the planner shall refuse the trip with the field name and a reason code.

**Terms:**

- TERM-001 Trip: A named journey with a destination, a start date and an end date, inclusive.

## Outputs

- COMP-001 Trip store: Persists trips, days, activities, expenses and bookings in one SQLite file, each change in one transaction.
- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-002): refuse the trip with the field name and a reason code when a trip name is empty or longer than 80 characters.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-001 (unit, normal) verifies REQ-001: A created trip returns its identifier, reads back with every field, and lists before older trips.
- [ ] TEST-002 (unit, refusal) verifies REQ-002: Empty and 81-character names are refused with field name and reason required or too_long; nothing is stored.

## Out of scope

- Accounts and logins: the planner runs locally for one household.
- Trip templates.
