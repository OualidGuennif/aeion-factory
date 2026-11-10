---
id: 010
sequence: 10
title: Pack without forgetting
goal: GOAL-010
area: planning
size: S
phase: P3
parallel: false
write_paths: ["app/"]
depends_on: [003]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 010 — Pack without forgetting

## Intent

Shared and personal packing lists everyone can check. Success measure: Checked items show as packed for every traveler.

Canonical source: `knowledge/spec/spec.json` GOAL-010 (spec `0a90103d634c`), requirements REQ-018, REQ-019.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Shared and personal packing items with a packed state everyone sees.

**Requirements:**

- REQ-018 (should, risk low): When a traveler adds a packing item, the planner shall list the item unchecked, shared or personal as chosen.
- REQ-019 (should, risk low): When a traveler checks a packing item, the planner shall mark it packed for everyone who sees that list.

## Outputs

- COMP-002 Domain rules: Validates trips, dates, activities, splits, places, bookings and status changes as pure functions.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-025 (unit, normal) verifies REQ-018, REQ-019: A shared item checked by Ana shows packed for Ben; a personal item shows only on its owner's list.

## Out of scope

- Packing templates per destination.
