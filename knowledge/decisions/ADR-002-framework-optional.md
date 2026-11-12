---
type: Decision
title: "ADR-002 AxiomSpec comes from aeion-framework, and only when the owner connects it"
description: "The embedded AxiomSpec engine is removed; framework mode reads the spec from an aeion-framework service, is off by default, and is switched on by the API address alone, never by a committed file."
status: stable
generated:
  by: aeion-template/4.0
  at: 2026-11-12
sources:
  - id: owner
    resource: "owner-message:2026-11-12 4.0.0 request"
    title: "Rename, remove the engine, framework optional and off by default, the address as the switch"
  - id: mode
    resource: ../components/framework-mode.md
    title: "Framework mode, its client and its briefs"
---

# ADR-002 — AxiomSpec comes from aeion-framework, and only when the owner connects it

## Context
Release 3.0.0 embedded an AxiomSpec engine (format `axiomspec/0.1`), a self-spec, a generated
cockpit and a demo, wired into pre-commit, CI, new projects and updates. The owner judged that this
went too fast: most projects start with uncodified specs. Meanwhile aeion-framework 1.1.9 serves
AxiomSpec over REST (`/v1`) and MCP (`/mcp/`) and no longer reads format 0.1, so the embedded engine
had already drifted from the framework it copied.

## Decision
The template carries no AxiomSpec engine. Component docs in the OKF format are the spec of every
project. A project specified with aeion-framework connects its service: framework mode is on if and
only if an API address is known, from `AEION_FRAMEWORK_URL` or the ignored `.aeion/settings.json`,
which only the owner writes (`tools/aeion-settings`). There is no separate boolean and no committed
switch; the committed `@req` annotations tell a teammate's clone that the code is specified, and
session start says how to connect. Agents read requirements through `tools/framework/axiom-api` and
the briefs the doc gate loads on a Read; they never edit requirements.

## Consequences
New projects start with nothing to install or learn; CI never needs the service. A 3.0.0 project
keeps its `knowledge/spec/` byte for byte and migrates it with the framework's scripts. The
supported range (1.1 up to 2.0, tested 1.1.9) lives in one constant the tech-watch moves. With
framework mode on and the service down, annotated files stay closed in `enforce` until it answers;
the owner can switch the gate to `warn`.

## Alternatives considered
- Keep the engine and follow the framework's format: two implementations of one spec, always behind.
- A committed `framework.json`: one clone's service address is not every clone's; it would also turn
  framework mode on in CI and for contributors without the service.
- A boolean beside the address: two facts that can disagree; the address alone cannot.
