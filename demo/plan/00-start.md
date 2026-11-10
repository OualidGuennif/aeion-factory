# Round 00: set up and read the spec

Every round refers to this protocol. Rounds 01-10 each build two features, in order.

## Do

1. Run the copy's own checks: `tools/factory-tests`, `tools/axiom/axiom check`,
   `tools/axiom/axiom validate`. Expect `design_ready: pass`.
2. From the factory's `demo/` folder, feed real hook payloads to the copy's hooks:
   `python3 <factory>/demo/batteries/hooks_battery.py <copy>`. Note which hooks your harness runs.
3. `tools/axiom/axiom export --all` into `docs/features/`, `tools/axiom/axiom docs`, and open
   `docs/README.md`: the open decision DEC-006 is listed; it does not block the first scope.
4. Answer in the journal: which requirement is formalized by a hard **project** rule, and why does
   every context packet carry it? (`tools/axiom/axiom query node CON-004`)

## The round protocol (rounds 01-10)

1. **Plan** (skill `plan`): the round's requirements, from `tools/axiom/axiom packet --ids ...`.
2. **Spec first** (skill `spec`): if the code needs an obligation the spec lacks, propose the
   requirement, test case or decision and wait for the owner. Each component gets its doc in
   `knowledge/components/` with `spec_ids` and `sources`; each code file its `Spec:` header.
3. **Tests first**, then thin slices (skills `test`, `build`), in `app/` and `app/tests/`.
4. **Bind and prove**: bindings `must_resolve`, test cases `implemented`,
   `tools/axiom/axiom evidence run --ids ...`, `tools/axiom/axiom docs`, `tools/axiom/axiom check`.
   Once a view's tests have receipts, its claim may become `observed`.
5. **Sign off** (skill `sign-off`): `CHANGELOG.md` line, `work/current.md`.

## Record block (end of every round)

```text
Result:          done | partial | blocked
Requirements:    REQ-... delivered; REQ-... not delivered (why)
Tests:           <n> receipts pass, <n> fail, <n> not executed (axiom evidence check)
Gates:           design_ready <status>; implementation_accepted <status> (G09 <s>, G10 <s>, G11 <s>)
Factory checks:  knowledge-check, doc-links, repo-health, axiom check: PASS | FAIL (rule)
Spec changes:    proposed / accepted (IDs), decisions asked
Guard refusals:  <n> (intent, rule, right or false positive)
Human help:      <n> (each time the owner had to act)
Elapsed:         <minutes>
```
