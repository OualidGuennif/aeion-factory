# Architecture Overview

These diagrams show how the Feature Cockpit (`/`), Model Lab (`/lab`), Flue + Pi agent harness, OpenShell sandboxes, and telemetry pipeline fit together. Full component specifications live in [`knowledge/index.md`](../../knowledge/index.md).

## End-to-end feature build flow

```mermaid
flowchart LR
  Owner["Operator\nFeature Cockpit (/)"] -->|"1. Queue ready feature"| Controller["Python Controller\n127.0.0.1:8088"]
  Controller -->|"2. Reserve budget\n($150/day cap)"| Ledger[("Spend Ledger\nledger.jsonl")]
  Controller -->|"3. Spawn session"| Harness["Flue 2.3 + Pi 1.4\nHost Harness"]
  Harness <-->|"Tool calls over mTLS"| Sandbox["OpenShell 0.1.8\nNetwork-isolated Sandbox"]
  Harness <-->|"Metered model calls"| Relay["Counting Relay\n230k/250k/300k bounds"]
  Relay <-->|"OpenCode Go / API"| Provider["Model Provider"]
  Sandbox -->|"4. Candidate tree"| Gate["Protected Check Gate\nDocker --network none"]
  Gate -->|"5. Verified diff"| Review["Two Independent Reviewers\nDistinct model families"]
  Review -->|"6. Approved"| PR["Product Pull Request\nExact-head CI -> main"]
```

## Telemetry and continuity pipeline

```mermaid
flowchart TD
  subgraph Workload["Host & Sandbox Execution"]
    Controller["Python Controller"]
    Relay["Counting Relay"]
    Harness["Flue + Pi Observer"]
  end

  subgraph Audit["Local Durable State (demo/.local/)"]
    JSONL[("Sequenced Audit JSONL")]
    Checkpoints[("SHA-256 Handover Checkpoints")]
    SQLite[("Factory SQLite Store")]
  end

  subgraph Observability["Local Docker Stack (Metadata Only)"]
    OTel["OpenTelemetry Collector\nRedaction & allowlist"]
    Langfuse["Langfuse 4.75\nTraces, costs & scores (:3300)"]
    Hindsight["Hindsight 1.2\nAdvisory session recall (:9999)"]
  end

  Workload -->|"fsync before export"| JSONL
  Workload -->|"230k / 250k handover"| Checkpoints
  Controller --> SQLite
  Workload -->|"Allowlisted OTLP spans"| OTel
  OTel --> Langfuse
  Controller -->|"Sanitized run summary"| Hindsight
```

## Key boundaries

OpenShell sandboxes run with `--network none`, no host home mount, no Docker socket, and no provider keys. Model requests leave only from the host through the counting relay.

Candidate code runs inside a fresh, network-isolated container whose test suite the author agent cannot inspect or modify.

Before spans reach Langfuse, the OpenTelemetry collector drops prompts, source code, tool payloads, and hidden reasoning so only timing, token counts, and event metadata leave the host harness.
