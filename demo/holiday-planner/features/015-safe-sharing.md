---
id: 015
sequence: 15
title: Share the plan safely
goal: GOAL-015
area: sharing
size: M
phase: P4
parallel: false
write_paths: ["app/"]
depends_on: [005, 013]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 015 — Share the plan safely

## Intent

A read-only link shows the itinerary to family and friends. Success measure: A link reveals nothing beyond the itinerary and stops working once revoked.

Canonical source: `knowledge/spec/spec.json` GOAL-015 (spec `0a90103d634c`), requirements REQ-027, REQ-028, REQ-029.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Issue 128-bit share tokens and revoke them.
2. Serve a read-only itinerary without money or codes (DEC-003).
3. Answer unknown and revoked tokens identically (404).

**Requirements:**

- REQ-027 (must, risk high): When an organizer creates a share link, the planner shall issue a random token of at least 128 bits that opens a read-only itinerary.
- REQ-028 (must, risk critical): If a share token is unknown or revoked, then the planner shall answer not found without revealing whether the trip exists.
- REQ-029 (must, risk high): The planner shall leave expenses, balances and booking codes out of shared views.

**Terms:**

- TERM-006 Share token: A random string of at least 128 bits that opens one trip's read-only itinerary until revoked.

**Decisions:**

- DEC-003 What may a read-only share link show? -> itinerary, places and packing list, no money or codes

## Outputs

- COMP-003 HTTP API and server: Serves the JSON API, the pages and the health check; maps refusals to stable status codes.
- COMP-005 Sharing: Issues, checks and revokes share tokens and builds the shared view.
- Refusal (REQ-028): answer not found without revealing whether the trip exists when a share token is unknown or revoked.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-039 (unit, normal) verifies REQ-027: A token decodes to at least 16 random bytes; 1000 tokens are all distinct.
- [ ] TEST-040 (integration, refusal) verifies REQ-028: A revoked token and a never-issued token both answer 404 with byte-identical bodies.
- [ ] TEST-041 (integration, refusal) verifies REQ-029: The shared itinerary holds activities and places, and no expense, balance or confirmation code.
- [ ] TEST-042 (e2e, normal) verifies REQ-027, REQ-028, REQ-029: An organizer shares a trip; the link shows its itinerary and offers no editing control.
- [ ] TEST-043 (unit, refusal) verifies REQ-027: Any write attempted with a share token is refused; the trip is unchanged.

## Out of scope

- Expiring links.
- Editing through a link.
