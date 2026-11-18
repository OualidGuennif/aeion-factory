# Æion Factory

Æion Factory is the autonomous build and observability workspace for the Æion ecosystem. It pairs an offline evaluation suite (`examples/`) with an opt-in local runtime (`demo/`) where coding agents implement, test, review, and publish product features inside isolated sandboxes.

Start at the [knowledge index](knowledge/index.md) and the [observability specification](knowledge/components/observability.md).

## Core principles

1. Verified work beats raw speed or price. A clean, unassisted pass that clears protected checks outranks a faster or cheaper run that fails checks or needs manual rescue.
2. Default telemetry exports metadata only. Prompts, source code, hidden reasoning, tool payloads, and secrets stay out of OTLP spans and local audit logs.
3. Spending and context are capped on the host. Each daily purse enforces `$150.00/day` (`$50.00` per author run, `$1.00` per review vote) in [`demo/budget.conf`](demo/budget.conf). Active input context hands over to a fresh agent session at `250,000` tokens (`300,000` hard cap).
4. Checks and reviews run independently of the author. Candidate diffs are verified in a container with `--network none` and reviewed by two distinct model families before any pull request can merge.
5. Unknown states fail closed. Missing usage data, stale sandbox proofs, or unqualified capabilities pause admission rather than guessing.

## What is in this repository

| Path | Purpose |
| --- | --- |
| [`knowledge/index.md`](knowledge/index.md) | Canonical architecture, component specs, policies, and runbooks |
| [`knowledge/components/observability.md`](knowledge/components/observability.md) | Event contract, privacy tiers, cost accounting, and routing rules |
| [`knowledge/components/operator-cockpit.md`](knowledge/components/operator-cockpit.md) | Feature Cockpit (`/`) and Model Lab (`/lab`) specification |
| [`knowledge/components/factory-flue.md`](knowledge/components/factory-flue.md) | End-to-end feature execution, two-reviewer circuit, and PR publication |
| [`demo/README.md`](demo/README.md) | Local pilot runbook: OpenShell 0.1.8, Flue 2.3.1 + Pi 1.5.2, Langfuse, and Hindsight |
| [`examples/README.md`](examples/README.md) | Offline synthetic fixtures, cohort comparisons, and deterministic guards |
| [`docs/architecture/high-level.md`](docs/architecture/high-level.md) | High-level system and data-flow diagrams |
| [`work/validation.md`](work/validation.md) | Dated verification records and test evidence |

## Quick checks without external services

The root test suite uses Python 3 standard library tooling and runs offline without Docker, network access, or API keys:

```sh
python3 examples/compare_cohorts.py
python3 examples/validate_fixtures.py
python3 -m unittest discover -s tests -v
tools/knowledge/knowledge-check && tools/knowledge/doc-links && tools/repo-health/repo-health
tools/template-tests
```

## Local Feature Cockpit and Model Lab (`demo/`)

The opt-in local controller serves two sidebar-driven monochrome views on `http://127.0.0.1:8088/`:

- The Feature Cockpit (`/` and `/factory`) unlocks with `demo/.local/factory/admin.token` so you can browse the 100 Agora specs (10 per page), launch isolated Flue + Pi builds in OpenShell, inspect queued or historical builds (5 per page), and track the `$150/day` budget ledger.
- The Model Lab (`/lab`) runs frozen JavaScript sandbox tasks, replays the 250k token handover, compares model cost against elapsed time, and queries local SHA-256 checkpoints or Hindsight session notes.

See [`demo/README.md`](demo/README.md) for setup, qualification, and shutdown instructions.

## How work flows here

1. Read the covering spec in [`knowledge/`](knowledge/index.md) before editing code (`tools/knowledge/doc-links --for <file>`).
2. Make small, tested changes on `develop`. Local hooks check secrets, syntax, and documentation links as you edit and commit.
3. Record an independent review and dated test evidence in [`work/validation.md`](work/validation.md) before pushing `develop` or merging to `main`.
