---
id: 012
sequence: 12
title: Find the places of the trip
goal: GOAL-012
area: planning
size: S
phase: P3
parallel: false
write_paths: ["app/"]
depends_on: [001]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 012 — Find the places of the trip

## Intent

Saved places with coordinates and a map link. Success measure: Every saved place opens on a map at its coordinates.

Canonical source: `knowledge/spec/spec.json` GOAL-012 (spec `0a90103d634c`), requirements REQ-021, REQ-022.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Save places with integer microdegrees and an OpenStreetMap link.
2. Refuse out-of-range coordinates.

**Requirements:**

- REQ-021 (should, risk low): When a traveler saves a place with a name and coordinates, the planner shall store latitude and longitude as integer microdegrees and offer a map link.
- REQ-022 (must, risk medium): If a latitude is outside -90..90 degrees or a longitude outside -180..180 degrees, then the planner shall refuse the place with the field and a reason code.

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.
- Refusal (REQ-022): refuse the place with the field and a reason code when a latitude is outside -90..90 degrees or a longitude outside -180..180 degrees.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-029 (unit, normal) verifies REQ-021: Paris at 48.8566, 2.3522 is stored as 48856600 and 2352200 microdegrees with a map link to those coordinates.
- [ ] TEST-030 (unit, refusal) verifies REQ-022: Latitude 91 and longitude -181 are refused with their field.

## Out of scope

- Geocoding or any call to a map API.
