---
type: Policy
title: "How code is written here"
description: "Steps that read top to bottom, comments that say why, no needless abstraction, and the branch, pull request and review flow."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: guide
    resource: ../../efficiency/1-quarks.md
    title: "Phase 1 of the guide"
---

# How code is written here

## Code reads top to bottom

A function that chains steps writes them one after the other, one call per step, each preceded
by a one-line comment saying the step's intent (a level above the code, never a paraphrase).

```ts
// Read the request; never re-fetch it here.
const order = parseOrder(request.body);
// Price it with the rules in force today.
const total = priceOrder(order, rules);
// Fail closed: an unreadable total is a refusal, never a guess.
return totalOrRefusal(total);
```

Not done here: one line chaining several steps; a helper around a single call; an interface with
one implementation; a "Manager", "Factory" or "Helper" without two real users; a parameter added
"in case". Allowed: a deep function whose name says everything and which hides real complexity.

## Comments

| Where | At most | What it says |
| --- | --- | --- |
| File or class header | 10 lines | what it is for, its authority boundary, `Spec: knowledge/<doc>.md` |
| Public method | 6 lines | its contract: inputs, output, refusals |
| Inside a function | 1 line per step (3 for a non-obvious trap) | the intent, or the why |

Never in a comment: dates, ticket numbers, the story of a bug, or a list of what is not done. The
story goes in the commit message.

`repo-health` applies source-size/comment heuristics to its documented suffix set and to
extensionless files that start with a shebang (`#!`), excluding `test_*` files. Its JSON scorecard reports that set and how many files were checked. This is a
structural scorecard; each project's build, linter and tests provide language-specific validation.

## Branch, review, release

This is the team flow, under git only. In a plain folder there is no branch, review, CI or tag: the
tests for what changed and the `CHANGELOG.md` line are the whole ritual. In local mode
(`git config aeion.mode local`, see [build and test](../operations/build-and-test.md)) commits stay
local, without review, CI or a `work/current.md` entry, and pre-push lets the user's own push through;
tests for what changed still run.

- Daily work is committed on `develop`; a parallel session uses a worktree on `task/<slug>` cut from
  `develop` and merges back locally. Small commits, each with its `CHANGELOG.md` line under Unreleased.
- Before each push of `develop`, the skill `pr-review` reviews `origin/develop..HEAD` with a fresh
  subagent, verifies every finding and records `Review: OK` or `Review: NOT OK` (at most five findings)
  for the exact commit in `.aeion/reviews/<sha>.md`, then posts it on the commit. The hook
  `tools/git-hooks/pre-push` (`git config core.hooksPath tools/git-hooks`) refuses a push of `develop`
  without `Review: OK` and any direct push to `main`. CI runs only for `main` and for pull requests,
  so pushes stay free. A loop's pull request into `develop` merges after its `Review: OK` comment and a
  green CI; then the local `develop` pulls it before new commits.
- A release (skill `ship`): `tools/release/release <part>` bumps `VERSION` (SemVer) and dates the
  changelog; a pull request `develop → main` is reviewed again and merged with a merge commit after a
  green CI; the merged commit is tagged `vX.Y.Z` with its changelog section as release notes.
- A deploy or a human decision waits for that human. The owner's comments become preferences
  (skill `pr-taste`).
- Limit: the review record is written by the agent that ran the review; the hook checks that one
  exists for the exact commit, not how it was produced.

## Before changing code

Locate the current owner of the behaviour, its tests and its spec; change the minimum; keep
existing contracts unless the task requires changing them. No abstraction is created "for later".
