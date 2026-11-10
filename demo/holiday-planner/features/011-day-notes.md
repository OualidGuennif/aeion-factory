---
id: 011
sequence: 11
title: Keep notes for each day
goal: GOAL-011
area: planning
size: S
phase: P3
parallel: false
write_paths: ["app/"]
depends_on: [004]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 011 — Keep notes for each day

## Intent

Plain-text notes per day, safe to display. Success measure: Notes display exactly as typed and never run as code.

Canonical source: `knowledge/spec/spec.json` GOAL-011 (spec `0a90103d634c`), requirements REQ-020.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Plain-text notes per day, escaped wherever they are shown.

**Requirements:**

- REQ-020 (must, risk high): The planner shall render day notes as plain text, never as HTML.

## Outputs

- COMP-004 Web pages: Renders the trip, day timeline, shared view and forms, escaping every value.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-026 (unit, refusal) verifies REQ-020: A note holding <script> renders as the literal text &lt;script&gt;.
- [ ] TEST-027 (unit, normal) verifies REQ-020: A note with accents and line breaks renders the same characters and line breaks.
- [ ] TEST-028 (e2e, refusal) verifies REQ-020: The served day page shows the note's markup as text and holds no injected element.

## Out of scope

- Rich text and attachments.
