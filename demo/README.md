# Demo: the Holiday Planner, specified with AxiomSpec

An agent builds a real product, **Holiday Planner**, inside a copy of Æion Factory, starting from a
canonical AxiomSpec specification instead of loose briefs. Twenty features, each one goal of
[`holiday-planner/knowledge/spec/spec.json`](holiday-planner/knowledge/spec/spec.json), are built in
ten rounds. Python's standard library only: an HTTP server, SQLite and a hand-written web interface.

The demo proves two things: the factory's AxiomSpec layer works end to end (`check`, no agent
needed), and a coding agent can deliver a product against checked obligations (the rounds).

## The self-check, in six seconds

```bash
demo/check            # 17 steps on a fresh copy; exit 0 when all pass
demo/check --keep     # keep the copy (its path is printed) to look around or start a round there
demo/check --refresh  # rewrite holiday-planner/features/ after changing the spec, then check
```

It creates a new project from the factory, installs the Holiday Planner's spec, and checks every
step: design gates G01-G07 (with BCIR scenarios), the cockpit and its six diagrams, the export of
the 20 feature files (eight sections, checkable acceptance items, under 12,000 bytes), graph
queries and the context packet of a change, a reference slice whose bindings resolve and whose
tests run through the evidence adapter, and three faults the checks must catch: stale evidence, a
dangling ID and a hand-edited generated page. `tools/factory-tests` runs it too.

## The product

| | |
| --- | --- |
| Brief | [`holiday-planner/docs/authored/brief.md`](holiday-planner/docs/authored/brief.md) |
| Canonical spec | 20 goals, 39 requirements, 60 test cases, 4 BCIR constraints, 7 scenarios, a lifecycle model, 6 decisions (one open on purpose) |
| Feature files | [`holiday-planner/features/`](holiday-planner/features/), exported by `tools/axiom/axiom export`, the format a build factory receives |
| Diagrams | [`holiday-planner/docs/views/`](holiday-planner/docs/views/): context, components, plan a day, add an activity, use cases, trip lifecycle |
| Reference slice | [`holiday-planner/reference/`](holiday-planner/reference/): the day schedule (features 005-006), used by the self-check |

## Run it with a coding agent

1. `demo/check --keep` and note the copy's path, or make a copy yourself: copy the factory without
   `demo/`, run `tools/release/release --new-project` in it, then copy the Holiday Planner's
   `knowledge/spec/spec.json`, `docs/` catalogs, views and brief into it (`demo/check` shows how).
2. Open the agent **in the copy** (it is a plain folder, so the copy's own hooks and instructions apply)
   and give it [`plan/START.md`](plan/START.md) as the first message, then one round at a time:
   [round 00](plan/00-start.md), then rounds 01 to 10.
3. Each round ends with the same record block, so harnesses can be compared. Keep the journal and
   feedback beside the copy, in `demo/runs/<harness>-run-NN/` (create it; `workspace/` stays ignored).

## Results by harness

| Harness | Factory | Rounds done | Design ready | Tests with receipts | Human help | Run |
| --- | --- | --- | --- | --- | --- | --- |
| (none yet) | 3.0.0 | | | | | |

Earlier demos (the Idea Board, factory 1.x-2.x) remain readable at tag `v2.1.1`.
