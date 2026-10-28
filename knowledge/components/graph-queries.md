---
type: Component
title: "Code graph queries"
description: "tools/architecture/ask: a working Graphify graph rebuilt when files change, and exact, deterministic answers to the structural questions an agent asks before reading code."
status: draft
generated:
  by: aeion-factory/1.3
  at: 2026-10-28
sources:
  - id: ask
    resource: ../../tools/architecture/ask
    title: "Query command and working-graph rebuild"
  - id: graph
    resource: ../../tools/architecture/graph.py
    title: "Structural extraction and the factory's added edges"
  - id: tests
    resource: ../../tools/architecture/tests/test_ask.py
    title: "Invariant tests"
  - id: skill
    resource: ../../.claude/skills/graph/SKILL.md
    title: "How an agent uses it"
---

# Code graph queries

## Intent
An agent should know where something is, what depends on it, which tests reach it and which spec
covers it before it reads code. Reading whole folders to find out costs tokens and misses links.

`tools/architecture/ask` answers those questions from a Graphify graph of the **working tree**. The
graph is rebuilt only when a project file changed. Every answer is exact, deterministic and names
`file:line`.

It complements the per-commit baselines of [architecture maintenance](../operations/architecture-maintenance.md),
which stay immutable and feed Archify. Intent and rules still come from `knowledge/` first: see the
`graph` skill.

## Data sources
| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| Project files | `project_files(root, untracked=True)`: git's list, or the plain-folder walk | the project | each call (fingerprint) |
| Graphify 0.9.97 | native AST, Markdown and config extraction; no LLM | `tools/architecture/requirements.txt` | pinned |
| Spec frontmatter `sources` | `specifies` edges, spec → file | knowledge docs | each rebuild |
| `Spec:` comment lines (first 20 lines, the line holds only the pointer, as `doc-links` reads it) | `specified_by` edges, file → spec | each code file | each rebuild |
| Test files' text | `names_file` edges when a test names a project path literally (scripts run as subprocesses) | the tests | each rebuild |
| `deno info --json` | exact `imports` edges of a Deno project, when `deno` and `deno.json` exist | Deno toolchain | each rebuild |

## Inputs
`ask [--root DIR] [--json] [--all] <command> [args]`. A name is a file path relative to the root, a
symbol label (`checkpoint_call()`), or a node id.

| Command | Question |
| --- | --- |
| `status` | Is the graph fresh, how big is it, which files yielded no symbol? |
| `find <name>` | Where is it defined? |
| `deps <name>` / `rdeps <name> [--depth N]` | What does it use? What breaks if it changes? |
| `path <A> <B>` | How does A reach B, hop by hop? |
| `tests <file>` | Which tests reach this file, and how? |
| `untested` | Which source files does no test reach? |
| `spec <file>` / `files <spec>` | Which spec covers this file? Which files does this spec cover? |
| `hubs [--top N]` | Where should a newcomer start? |

## Outputs
- **Text** (the default) is at most 40 result lines, each with `file:line`. `--all` lifts the cap,
  and a truncated answer says how many lines it hid.
- **`--json`** returns one object: `{"command", "graph": {"fingerprint", "rebuilt", "nodes", "edges"}, "results": [...]}`.
- **Exit codes:**
  - 0: an answer, even an empty one, which is stated;
  - 3: an ambiguous name, with its candidates listed;
  - 4: no node matches;
  - 2: a usage error;
  - 1: the graph cannot be built, for example when the Graphify venv is missing (the message names
    `tools/architecture/setup`).
- The graph lives in `.aeion/graph/`, which is ignored: `graph.json`, `coverage.json` and `fingerprint`.

## Invariants
| Invariant | Test |
| --- | --- |
| A name matches exactly (path, label, label without `()`, or id). Several matches give exit 3, none gives exit 4, and nothing is guessed. | `test_names_match_exactly` |
| The graph is rebuilt if and only if the files' fingerprint (path, size, mtime) changed. | `test_rebuild_only_on_change` |
| `path` names a hop with no edge instead of skipping it, and prefers imports, then calls. | `test_path_names_each_hop` |
| `tests` and `untested` tell a test that imports a file from one that reaches it through others or names it. | `test_tests_and_untested` |
| `spec` reports each spec from frontmatter and from the `Spec:` comment line; it marks a gap (a code file with no `Spec:` line, or a `Spec:` line the spec's sources omit) and a file shared by two specs, never a conflict. A file no extractor reads still resolves. | `test_spec_both_directions`, `test_real_build_adds_spec_line_and_test_name_edges` |
| `hubs` leaves out tests, documents and external modules. | `test_hubs_exclude_noise` |
| Output order is stable: sorted, never in dictionary order. | `test_output_is_stable` |
| No language model is called. The build is `graph.py` (AST only), and `guard-bash` refuses Graphify's LLM commands. | `test_hooks.py`: graphify LLM commands |

## Determinism
- Same files give the same graph and the same answers. Sorting is by path, then line, then label.
- `deno info` is the only external process, and it is used only for a Deno project. When it is
  missing, `coverage.json` records `toolchain_imports: "unavailable"` and no edge is invented.
- Queries use only the Python standard library on `graph.json`, so a query does not start the venv.

## Acceptance checks
```bash
python3 tools/architecture/tests/test_ask.py
tools/architecture/ask status
tools/architecture/ask rdeps tools/context/budget.py
tools/architecture/ask tests .claude/hooks/guard-bash.py
```

## Out of scope
- **Type-resolved calls** (a method called on an object received as a parameter): the language server
  answers those (the `graph` skill routes them to LSP `findReferences`).
- **An MCP server.** A query costs about 50 ms, and a rebuild about 1 s on 155 files. A resident
  server would hold a graph that goes stale as files are edited.
- Graphify's LLM extraction, community labels and SCIP ingestion. SCIP ingestion is an unwired
  skeleton in 0.9.97.
