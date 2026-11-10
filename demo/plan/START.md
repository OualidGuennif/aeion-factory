# First message for the agent

You are building the Holiday Planner in this folder, a copy of Æion Factory 3.0.0. Read `AGENTS.md`,
then `knowledge/axiomspec/index.md` and the skill `axiom`. The product's obligations are in
`knowledge/spec/spec.json`; the 20 feature files in `docs/features/` (run `tools/axiom/axiom export
--all` once) are their readable form, and `docs/README.md` is the cockpit.

Rules for every round:

- The spec decides. Before code, read `tools/axiom/axiom packet --ids <the round's REQ IDs>`. A
  blocking decision without an answer is a question for me, never a guess. A missing obligation is a
  proposed spec change (requirement, test case, decision), shown to me before the code.
- Python 3 standard library only, in `app/` (tests in `app/tests/`, `unittest`). No dependency, no
  network call, no build step.
- When code and tests land: set the bindings to `must_resolve` and the test cases to `implemented`,
  run `tools/axiom/axiom evidence run --ids <TEST IDs>`, `tools/axiom/axiom docs`, then
  `tools/axiom/axiom check` and `tools/axiom/axiom validate --phase implementation`. Report unknown
  as unknown.
- End each round with the record block of `demo/plan/00-start.md`.

Start with round 00 only, and wait for me before round 01.
