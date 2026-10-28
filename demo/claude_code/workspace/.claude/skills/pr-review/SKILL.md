---
name: pr-review
description: Reviews a change with a fresh subagent, verifies every finding, and records one short verdict (Review OK or NOT OK with at most five findings and file:line). Use before each push of develop, on each release pull request, and after each push of fixes.
---

# Review a change

## Overview
A fresh context catches what the author's context hides. One comment, one verdict. Flow: `knowledge/policies/engineering.md`.

## Process
Two targets, same review. **Develop push:** the range `origin/develop..HEAD` (`git log`, `git diff`).
**Release:** the pull request `develop → main` (`gh pr view <n>`, `gh pr diff <n>`, `gh pr checks <n>`).
1. Collect the diff and the files it touches.
2. Start ONE fresh, read-only reviewer subagent with: the diff, `AGENTS.md`, and the docs
   `tools/knowledge/doc-links --for <file>` names. Ask for findings ranked by severity, each with path:line
   and a concrete failure scenario.
3. A sensitive diff: also skill `security-scan` on the changes, or say it was not run.
4. Verify every finding yourself; drop what you cannot confirm.
   Trace suggestions against the code/spec before implementing them; disagree with an unsupported
   fix. For context/architecture work, verify claimed guarantees and exact-SHA artifact coverage.
5. Write the verdict, first line exactly `Review: OK` or `Review: NOT OK`:
   ```
   Review: OK            (or)   Review: NOT OK
   - <high|medium|low> path:line -- the finding (at most five)
   Checks: CI <state or "not run (develop)">; doc-links <result>; tests <what ran>
   ```
   - Develop push: save it as `.aeion/reviews/<full HEAD sha>.md` (ignored; `tools/git-hooks/pre-push`
     reads it), then after the push post it on the commit:
     `gh api repos/{owner}/{repo}/commits/<sha>/comments -F body=@.aeion/reviews/<sha>.md`.
   - Release: save it as `.aeion/loop-bodies/review-<n>.md` (the only body path read-only loops may
     publish) and `gh pr comment <n> --body-file .aeion/loop-bodies/review-<n>.md`.
   - Loop pull request into `develop`: as a release, on the PR; it merges after Review OK and a green CI.
6. NOT OK: fix, commit, review again; a new commit needs a new verdict. Release OK and CI green: the
   skill `ship` merges. A human decision waits before the merge; a deploy after it.

## Rationalizations
| Excuse | Rebuttal |
| --- | --- |
| "I wrote it, I know it's fine" | That is why the reviewer is fresh. |

## Red flags
Approving through the forge's review API; merging on red CI; a secret in a comment.

## Verification
- [ ] The verdict is recorded for the exact commit (develop) or on the PR (release), with the checks line.
