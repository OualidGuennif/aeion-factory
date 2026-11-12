---
type: Reference
title: "Æion Template integration choices"
description: "The narrow upstream practices retained for context safety and skills, and why the template embeds no spec engine: AxiomSpec belongs to aeion-framework."
status: stable
generated:
  by: aeion-template/3.0
  at: 2026-11-10
sources:
  - id: context
    resource: ../operations/context-safety.md
    title: "Actual context contract"
  - id: architecture
    resource: template-architecture.md
    title: "Complete architecture specification"
---

# Integration choices

The approved plan preserves Doc / OKF / Knowledge, frontmatter/tags, Æion Template skill entry points,
existing hooks and the reviewed task flow. Current behavior belongs to the linked runbooks and
architecture specification; this file records the integration choices rather than a second policy.

## Context-mode

[Inspected source](https://github.com/mksglu/context-mode/tree/8b74cbba68a79e45170dd5866dee949fd6ddd8e1).
Retain bounded output, processing large results in code, file artifacts and handover restoration.
No upstream code/MCP/memory store is installed. Its best-effort snapshot is not a deterministic
340k/390k token guard. Æion Template uses native compaction at 340k, explicit closure and a verified
checkpoint; the 390k forced compaction is not qualified pre-request admission. Strict execution
refuses instead of claiming an unsupported guarantee.

## Superpowers

[Inspected source](https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b).
Add focused debugging; strengthen the existing plan, test, sign-off and review procedures.
Reproduction, one falsifiable hypothesis, meaningful regression evidence and fresh verification
add value. Existing build/spec/review/ship behavior already covers much of the rest. Do not add
the global bootstrap, mandatory implementer/reviewer rounds or a second task ledger. Worktrees
and additional agents remain justified by actual independent work, not enabled by default.
Adapted material retains its MIT attribution in CREDITS and the accompanying notice.

## No embedded spec engine (4.0)

Up to 2.1, a pinned Graphify extracted a structural code graph and Archify rendered diagrams; both
needed a virtual environment, Node and a browser, and 3.0 removed them. 3.0 then embedded AxiomSpec
(edition 0.3.0, format `axiomspec/0.1`) with its own engine, made it mandatory, and drifted: the
framework moved to format `axiomspec/0.3`, stopped testing that engine, and its service refuses 0.1.
4.0 removes the engine. The method, its engine and its service belong to aeion-framework; the
template keeps its OKF docs and, only when the owner gives an API address, reads the project's spec
through that service. Diagrams are Mermaid written by hand in Markdown: the reader's platform draws
them, so nothing renders at build time and nothing is installed.

Rejected: keeping the 0.1 engine as an offline option (a second implementation to port and maintain,
and two answers that can disagree); vendoring the 1.1.9 package (its CLI needs Python 3.14, and the
service already answers agents with bounded, paged results).

No new database, service, scheduler, provider router or agent orchestration layer is introduced.
