---
id: 018
sequence: 18
title: See a day at a glance
goal: GOAL-018
area: interface
size: L
phase: P4
parallel: false
write_paths: ["app/"]
depends_on: [005, 006]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 018 — See a day at a glance

## Intent

A clear time grid for each day, usable by everyone. Success measure: The day view matches the stored activities and passes the accessibility review.

Canonical source: `knowledge/spec/spec.json` GOAL-018 (spec `0a90103d634c`), requirements REQ-033, REQ-034.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Draw each day as a time grid, activities sized by duration and coloured by category.
2. Make every page keyboard-usable with visible focus and AA contrast.

**Requirements:**

- REQ-033 (should, risk medium): The planner shall show each day as a time grid with activities sized by duration and coloured by category.
- REQ-034 (must, risk medium): The planner shall keep every page usable with a keyboard alone and at WCAG 2.2 AA contrast.

## Outputs

- COMP-004 Web pages: Renders the trip, day timeline, shared view and forms, escaping every value.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-048 (e2e, normal) verifies REQ-033: The day page places a 90-minute activity at 09:00 over three half-hour rows, coloured by its category.
- [ ] TEST-049 (manual, normal) verifies REQ-034: A reviewer completes every flow with the keyboard alone and measures contrast of 4.5:1 or more on text, with notes.
- [ ] TEST-050 (e2e, refusal) verifies REQ-034: Every interactive element of the main pages is reachable by Tab and has a visible focus style.

## Out of scope

- Drag and drop.
