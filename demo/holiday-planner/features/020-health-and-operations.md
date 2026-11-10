---
id: 020
sequence: 20
title: Run it with confidence
goal: GOAL-020
area: operations
size: S
phase: P5
parallel: false
write_paths: ["app/"]
depends_on: [001]
status: proposed
spec_sha256: 0a90103d634c750ec9237f364f51041b65280abe8441a6ea89f9c922e50de2ed
generated_by: aeion-docs/3.0.0
---

# 020 — Run it with confidence

## Intent

Health, configuration and logs an operator can trust. Success measure: The health check reports storage, and logs hold no personal data.

Canonical source: `knowledge/spec/spec.json` GOAL-020 (spec `0a90103d634c`), requirements REQ-037, REQ-038, REQ-039.

## Data sources

- SRC-001 (document, reviewed): `docs/authored/brief.md`

## Inputs

**Delivery steps:**

1. Serve /health with storage status and version.
2. Read PORT and DATA_PATH; write scrubbed structured logs.

**Requirements:**

- REQ-037 (must, risk medium): When the health endpoint is called, the planner shall answer 200 with the storage status and the version.
- REQ-038 (must, risk high): The planner shall write logs without traveler names, notes, codes or amounts.
- REQ-039 (must, risk low): The planner shall read its port and data path from PORT and DATA_PATH, with safe local defaults.

## Outputs

- COMP-003 HTTP API and server: Serves the JSON API, the pages and the health check; maps refusals to stable status codes.
- COMP-007 Operations: Reads configuration and writes scrubbed structured logs.

## Invariants

- No formal constraint yet: the acceptance checks below are the contract.

## Determinism

Deterministic checks decide: the acceptance tests below and `tools/axiom/axiom validate`. A model's output is a proposal until those checks pass.

## Acceptance checks

- [ ] TEST-056 (integration, normal) verifies REQ-037: GET /health answers 200 with storage ok and the version.
- [ ] TEST-057 (unit, refusal) verifies REQ-038: A log record carrying a name, a note, a code and an amount is written without those values.
- [ ] TEST-058 (unit, normal) verifies REQ-038: Method, path template, status and duration remain in the log line.
- [ ] TEST-059 (integration, refusal) verifies REQ-038: After creating a trip with a traveler and a note through the API, the captured logs contain none of their values.
- [ ] TEST-060 (unit, normal) verifies REQ-039: PORT=9000 and DATA_PATH are read; without them the server uses 8000 and ./data/planner.sqlite3.

## Out of scope

- Metrics dashboards.
