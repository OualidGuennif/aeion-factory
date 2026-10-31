# Check: handover

## Success

- Command: `grep -n '^## ' work/handovers/session-<id>.md`
- Expected: exactly five headings, in the order Scope, Completed, Remaining, Constraints, Evidence
- Command: `git status --short`
- Expected: one untracked file under `work/handovers/`, nothing else
- Human judgment: every claim in Completed points at a path that exists, and Remaining is not empty.

## Failure

- A required command exits nonzero.
- The expected output differs from `Expected`.
- The diff touches an out-of-scope file from `TASK.md`.
- The run needs a fix after it reports done.

## Record

`--success yes` when every success line holds; `--success no` for any failure line.
