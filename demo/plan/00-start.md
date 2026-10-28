# 00 — Start: the Idea Board brief

Read this first. It is the brief every round refers to. The feature files `01`–`07` are built in
order, one round each, by an agent working inside a copy of Æion Factory **without git**.

## The product

**Idea Board** is a small team board. People propose ideas, vote for the ones they want, and
filter them by tag or text. It has no accounts: it is a playground, but a serious one, with real
validation, real persistence and tests.

| Actor | Wants to |
| --- | --- |
| Visitor | see the ideas, sorted by votes or by date, filter by tag, search by text |
| Contributor | propose an idea (title, description, tags), vote for an idea |
| Operator | run it locally or in Docker, know it is healthy, keep its data across restarts |

## Stack (use the latest stable version of each, and record the exact versions you used)

| Layer | Choice | Why |
| --- | --- | --- |
| Runtime | Deno 2 | one binary: runtime, test runner, formatter, linter, type checker |
| Web | Fresh 2 with its Vite plugin | server-side rendered pages, islands for the interactive parts |
| API | Hono, mounted under `/api` | a small, typed router; testable with `app.request()` without a server |
| Storage | Deno KV (SQLite file locally, `:memory:` in tests) | built in, atomic operations |
| Packaging | Docker + Compose on the official `denoland/deno` image | one command to run anywhere |

## Layout inside the factory copy

```
<factory copy>/
  app/                     the Deno + Fresh application (its own deno.json)
  knowledge/components/    one spec per feature, written before the code (skill `spec`)
  CHANGELOG.md             one Unreleased line per round
  work/current.md          the open round only
```

## How to run (the app must support all three by the end of round 06)

```bash
cd app && deno task dev                      # development, hot reload
cd app && deno task build && deno task start # production build, local
docker compose -f app/compose.yaml up --build    # container, with a persistent KV volume
```

## The round protocol (follow the factory, plain-folder mode)

1. Read the feature file. Write a short plan (skill `plan`): files touched, what will not be done.
2. Write or update the spec in `knowledge/components/` (skill `spec`, eight sections). Link it from
   `knowledge/components/index.md`. Each code file it covers carries a `Spec:` header line.
3. Write the acceptance tests first and see them fail, then build in thin slices (skills `test`, `build`).
4. Run the batteries:
   - app: `deno fmt --check`, `deno lint`, `deno check`, `deno test -A`, then the smoke commands from the feature file;
   - factory: `tools/knowledge/knowledge-check`, `tools/knowledge/doc-links`, `tools/repo-health/repo-health`.
5. Sign off without git (skill `sign-off`): the tests and docs are the whole sign-off, plus the
   `CHANGELOG.md` line and `work/current.md`.
6. Write down what happened: what you did, where you got stuck, what the framework helped with or got
   in the way of. A friction with the framework is a feedback for Æion Factory.

## Shared rules for every round

- Validation errors are stable JSON: `{"error": "invalid", "field": "<name>", "reason": "<code>"}`.
- No secret in the repository. Configuration comes from the process environment (`PORT`, `KV_PATH`), with safe defaults.
- User text is never rendered as HTML.
- A round is done only when every acceptance check of its file passes, with the command output kept.
