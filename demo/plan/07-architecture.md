# 07 — Architecture: Graphify use cases and an Archify gallery

## Goal
Make the finished app understandable at a glance, and show what a code graph is actually good for.

## Part A — Graphify (structural graph of the app)
Build the graph of `app/` and the `knowledge/components/idea-board-*.md` specs with the factory's
pinned Graphify (`tools/architecture/graph.py <root> <out> <manifest.json>`; it does not need git).
Then answer real questions with it, and keep each command and its real output in `graphify/use-cases.md`:

| Question a developer really asks | How |
| --- | --- |
| What breaks if I change the ideas store? | `graphify explain "<store node>"` (its dependents) |
| How does a `POST /api/ideas` reach KV? | `graphify path "<catch-all route>" "<store>"` |
| Which source files have no test file pointing at them? | a short script over `graph.json` |
| Which spec covers this file, and which file has none? | the Markdown → code links in the graph |
| Where should a newcomer start? | the most connected nodes |

## Part B — Archify gallery (many small diagrams of the whole program)
One page `index.html` with a card per diagram: title, the question it answers, a live thumbnail,
a link to the full diagram. Each diagram is small (at most about 10 boxes) and answers one question.

| Family | Diagrams |
| --- | --- |
| System | system overview (browser, Fresh server, islands, Hono API, domain, store, KV); Docker deployment |
| Sequence | page load (SSR); create an idea (island → API → validation → KV); vote (optimistic transaction with retry); filter and search; health check |
| Use case | Visitor; Contributor; Operator (actors outside, use cases inside the system boundary) |
| Other | idea lifecycle; KV key model; request data flow; the Æion round that built it |

Every diagram passes `archify validate` and `archify browser-check`. Archify has no "use case"
type: draw use cases as an `architecture` diagram (actors as external components, use cases as
components inside a boundary) and say so on the card.

## Acceptance checks
```bash
<factory>/.aeion/integrations/graphify-venv/bin/python tools/architecture/graph.py app <out>/graph <manifest.json>
node <archify>/bin/archify.mjs validate <type> diagrams/<name>.json --quality showcase
node <archify>/bin/archify.mjs render <type> diagrams/<name>.json diagrams/<name>.html --quality showcase
node <archify>/bin/archify.mjs browser-check diagrams/<name>.html --summary
```

## Out of scope
Archify evidence links (`sources`): they need a git revision and a repository URL, which a plain
folder does not have. LLM-inferred graph edges.

## Expected result
`render/index.html` opens offline, every card loads its diagram, and `graphify/use-cases.md`
answers the five questions with real output.
