# Graphify on the Idea Board: five real questions

The graph covers `app/` (code, `deno.json`, `compose.yaml`) and the three `idea-board-*` specs, as
listed in [`manifest.json`](manifest.json). It was built with the factory's pinned Graphify 0.9.95,
structural extraction only (no LLM inference), on the git-less copy:

```bash
W=demo/claude_code/workspace
.aeion/integrations/graphify-venv/bin/python tools/architecture/graph.py $W <out> manifest.json
# 205 nodes, 363 edges; 38 required source/docs files covered.
# warning: 5 code file(s) yielded no symbols: app/api/search_test.ts, app/api/votes_test.ts,
#          app/client.ts, app/routes/_app.tsx, app/vite.config.ts
```

Outputs kept here: [`graph.json`](graph.json), [`coverage.json`](coverage.json). Questions 3 to 5 are
answered by [`questions.py`](questions.py):
`python3 questions.py graph.json demo/claude_code/workspace`.

## 1. What breaks if I change the ideas store?
```bash
graphify explain "ideas.ts" --graph graph.json
```
```text
Node: ideas.ts
  Source:    app/store/ideas.ts L1
  Degree:    21
  <-- home.tsx [imports_from] [EXTRACTED] app/pages/home.tsx:L8
  <-- testing.ts [imports_from] [EXTRACTED] app/testing.ts:L6
  <-- app.ts [imports_from] [EXTRACTED] app/api/app.ts:L6
  <-- vote_test.ts [imports_from] [EXTRACTED] app/pages/vote_test.ts:L6
  <-- shared.ts [imports_from] [EXTRACTED] app/store/shared.ts:L3
  <-- app_test.ts [imports_from] [EXTRACTED] app/api/app_test.ts:L5
  <-- VoteButton.tsx [imports_from] [EXTRACTED] app/islands/VoteButton.tsx:L6
  <-- pages/vote.ts [imports_from] [EXTRACTED] app/pages/vote.ts:L4
  <-- store/search_test.ts [imports_from] [EXTRACTED] app/store/search_test.ts:L4
  --> idea.ts, createIdeaStore(), IdeaStore, Sort, VoteResult, ideaKey(), votesKey(), backoff(), …
```
**Answer.** Six production files depend on the store: the API (`app.ts`), both page handlers
(`home.tsx`, `pages/vote.ts`), the shared store (`shared.ts`) and, by its `Sort` type only, the
`VoteButton` island. A change to `ListOptions` or `Sort` reaches the client bundle; a change inside
`createIdeaStore()` does not. Three test files and `testing.ts` import it directly.

## 2. How does a `POST /api/ideas` reach KV?
```bash
graphify path "[...path].ts" "createApi()"         --graph graph.json
graphify path "createApi()" "validateNewIdea()"    --graph graph.json
graphify path "[...path].ts" "kv.ts"               --graph graph.json
graphify path "app.ts" "createIdeaStore()"         --graph graph.json
```
```text
[...path].ts --imports [EXTRACTED]--> createApi()
createApi() --calls [EXTRACTED]--> validateNewIdea()
[...path].ts --imports_from [EXTRACTED]--> shared.ts --imports_from [EXTRACTED]--> kv.ts
app.ts --imports_from [EXTRACTED]--> ideas.ts --contains [EXTRACTED]--> createIdeaStore()
```
**Answer.** The Fresh catch-all route `routes/api/[...path].ts` builds the Hono app with
`createApi()` and hands it the shared store. `createApi()` validates with `validateNewIdea()`, then
calls the store's `create`, which `createIdeaStore()` defines over the KV that `kv.ts` opens. The
graph has no edge for the `ideas.create(...)` call itself: it is a method on an object returned by a
function, which structural extraction does not resolve. The sequence diagram "Create an idea" in
the gallery draws the full path.

## 3. Which source files have no test file pointing at them?
| File | A test imports it | A test reaches it |
| --- | --- | --- |
| `app/client.ts` | no | **no** |
| `app/components/IdeaFormFields.tsx` | no | yes |
| `app/islands/NewIdeaForm.tsx` | no | yes |
| `app/islands/VoteButton.tsx` | no | yes |
| `app/main.ts` | no | **no** |
| `app/pages/home.tsx` | no | yes |
| `app/routes/_app.tsx` | no | **no** |
| `app/routes/api/[...path].ts` | no | **no** |
| `app/routes/ideas/[id]/vote.ts` | no | **no** |
| `app/routes/index.tsx` | no | **no** |
| `app/serve.ts` | no | **no** |
| `app/store/kv.ts` | no | **no** |
| `app/store/shared.ts` | no | **no** |
| `app/vite.config.ts` | no | **no** |

**Answer.** The first column alone overstates the gap: `home.tsx` is tested through
`testing.ts`'s `homeApp`, so the script follows edges from each test. What no test reaches is the
wiring: the route files, `main.ts`, `serve.ts`, the shared store and `kv.ts`. Each holds one or two
lines that pass the store to a handler. The HTTP smoke tests (rounds 02–05) and
`container_check.sh` (round 06) cover them, not `deno test`. `kv.ts` is the one with logic
(`KV_PATH`, the folder creation); a unit test for it is the cheapest real gain.

## 4. Which spec covers this file, and which file has none?
```text
knowledge/components/idea-board-api.md: 2 files: filters.ts, idea.ts
knowledge/components/idea-board-page.md: 4 files: filters.ts, form.ts, idea.ts, VoteButton.tsx
knowledge/components/idea-board-runtime.md: 0 files
```
| File | Spec in the graph | Spec in its header |
| --- | --- | --- |
| `app/api/app.ts` | none | idea-board-api |
| `app/client.ts` | none | **none** |
| `app/components/IdeaFormFields.tsx` | none | idea-board-page |
| `app/domain/filters.ts` | idea-board-api, idea-board-page | idea-board-api |
| `app/domain/form.ts` | idea-board-page | idea-board-page |
| `app/domain/idea.ts` | idea-board-api, idea-board-page | idea-board-api |
| `app/islands/NewIdeaForm.tsx` | none | idea-board-page |
| `app/islands/VoteButton.tsx` | idea-board-page | idea-board-page |
| `app/main.ts` | none | **none** |
| `app/pages/home.tsx` | none | idea-board-page |
| `app/pages/vote.ts` | none | idea-board-page |
| `app/routes/_app.tsx` | none | **none** |
| `app/routes/api/[...path].ts` | none | idea-board-api |
| `app/routes/ideas/[id]/vote.ts` | none | idea-board-page |
| `app/routes/index.tsx` | none | idea-board-page |
| `app/serve.ts` | none | idea-board-api |
| `app/store/ideas.ts` | none | idea-board-api |
| `app/store/kv.ts` | none | idea-board-api |
| `app/store/shared.ts` | none | idea-board-page |
| `app/testing.ts` | none | idea-board-api |
| `app/utils.ts` | none | **none** |
| `app/version.ts` | none | idea-board-api |
| `app/vite.config.ts` | none | **none** |

**Answer.** The graph alone gets this wrong. Its Markdown → code edges come only from code names
written in a spec's body (`parseFilters()`, `VoteButton`), so it links 6 files. Each spec's
frontmatter `sources` list, the factory's own spec ↔ code contract, is not turned into edges, and
the runtime spec links nothing. The repository's real answer is the `Spec:` header in each file: 18
of 23 source files name their spec. The five without one are the Fresh scaffold files (`client.ts`,
`main.ts`, `_app.tsx`, `utils.ts`, `vite.config.ts`). This gap is **FB-010**.

## 5. Where should a newcomer start?
```text
 32  home.tsx  (app/pages/home.tsx)
 21  ideas.ts  (app/store/ideas.ts)
 20  testing.ts  (app/testing.ts)
 19  app.ts  (app/api/app.ts)
 13  vote_test.ts  (app/pages/vote_test.ts)
 12  idea.ts  (app/domain/idea.ts)
 11  NewIdeaForm.tsx  (app/islands/NewIdeaForm.tsx)
 11  imports  (app/deno.json)
 11  createApi()  (app/api/app.ts)
 10  utils.ts  (app/utils.ts)
```
**Answer.** Read in this order: `domain/idea.ts` (what an idea is and what is refused),
`store/ideas.ts` (how it is kept), `api/app.ts` (the API over it), then `pages/home.tsx` (the
page). `testing.ts` ranks third because every page test goes through it; it is the place to learn
how to test a handler on an in-memory KV.

## After: the same questions with `tools/architecture/ask`
Replayed on 2026-10-28 with Graphify 0.9.97 and the skill `graph`, on the whole workspace (172 files,
1,217 nodes; first build about 2 s, then about 0.1 s per question). No script, no LLM, no server:

```bash
ask() { tools/architecture/ask --root demo/claude_code/workspace "$@"; }
```

| Question | Before (round 07) | After |
| --- | --- | --- |
| 1. What breaks if I change the store? | `explain` listed 9 direct importers, mixed with its own symbols | `ask rdeps app/store/ideas.ts --depth 2`: 9 direct importers, then 9 files at depth 2 (the routes and the tests through `app.ts` and `testing.ts`), each with `file:line` |
| 2. How does `POST /api/ideas` reach KV? | four `graphify path` calls, one of them silently matched to a different node | `ask path "app/routes/api/[...path].ts" app/store/kv.ts`: `[...path].ts:4` → `shared.ts:4` → `kv.ts`; the `ideas.create()` hop stays a method call: the skill sends it to the language server |
| 3. What has no test? | a 60-line script | `ask untested`: 8 app files reached by no test (the route wiring, `main.ts`, `serve.ts`, `shared.ts`, `kv.ts`, `container_check.sh`); `ask tests app/store/kv.ts` says "no test reaches" it. The three Fresh scaffold files have no symbol, so `status` lists them instead |
| 4. Which spec covers this file? | the graph linked 6 files, from body names only; FB-010 | `ask spec` reads both sides. 22 app files are `[both]`. `serve.ts` and `shared.ts` are shared: two specs list them, and each header names one, which `ask` states without calling it a conflict. The `Dockerfile` and `.dockerignore` resolve too (before, they were reported missing because no extractor reads them). The one gap left is `testing.ts`: it names the API spec, which does not list it |
| 5. Where to start? | the top nodes, with test files and `deno.json` keys | `ask hubs`: `store/ideas.ts` (used by 9 files), `testing.ts` (8), `utils.ts` (7), `api/app.ts` (5), `domain/idea.ts` (5); tests and configuration left out |

Exact names changed the failure mode. `graphify path` answered with a near match. `ask` answers
exit 3 with the candidates (`ask deps main`) or exit 4, and nothing is guessed. `deno info` drew 54 exact
imports, all already in Graphify's graph, so on this app the imports were complete; the gaps were
the spec contract, the test reach and the noise, which the answers above now close.
