#!/usr/bin/env python3
"""Answer three of the round 07 questions from a Graphify graph.json: untested files, spec coverage, entry points."""
import collections
import json
from pathlib import Path
import sys

graph = json.loads(Path(sys.argv[1]).read_text())
nodes = {node["id"]: node for node in graph["nodes"]}
links = graph["links"]


def file_of(node_id):
    return str(nodes[node_id].get("source_file", ""))


def is_test(path):
    return path.endswith(("_test.ts", "_test.tsx"))


def is_source(path):
    return path.startswith("app/") and path.endswith((".ts", ".tsx")) and not is_test(path)


# Every file-to-file edge, whatever node inside the file carries it.
file_edges = {(file_of(link["source"]), file_of(link["target"])) for link in links}
file_edges = {(a, b) for a, b in file_edges if a and b and a != b}
sources = sorted({file_of(node_id) for node_id in nodes if is_source(file_of(node_id))})

print("## Q3. Source files no test file points at")
tested = {target for origin, target in file_edges if is_test(origin)}
# A test also covers what it reaches through helpers such as testing.ts, so follow the edges.
reached = set(tested)
frontier = list(tested)
while frontier:
    current = frontier.pop()
    for origin, target in file_edges:
        if origin == current and target not in reached:
            reached.add(target)
            frontier.append(target)
print("| File | A test imports it | A test reaches it |")
print("| --- | --- | --- |")
for path in sources:
    if path not in tested:
        print(f"| `{path}` | no | {'yes' if path in reached else '**no**'} |")

print("\n## Q4. Which spec links to which source file")
specs = sorted({file_of(node_id) for node_id in nodes if file_of(node_id).endswith(".md")})
covered = collections.defaultdict(list)
for spec in specs:
    targets = sorted({target for origin, target in file_edges if origin == spec and is_source(target)})
    print(f"- {spec}: {len(targets)} files: {', '.join(Path(t).name for t in targets)}")
    for target in targets:
        covered[target].append(Path(spec).stem)
# The repository's own answer: each source file's "Spec:" header, which the graph does not model.
declared = {}
root = Path(sys.argv[2]) if len(sys.argv) > 2 else None
for path in sources:
    if root and (root / path).exists():
        head = (root / path).read_text().splitlines()[:3]
        declared[path] = next((line.split("Spec:")[1].strip() for line in head if "Spec:" in line), "")
print("\n| File | Spec in the graph | Spec in its header |")
print("| --- | --- | --- |")
for path in sources:
    graph_side = ", ".join(covered.get(path, [])) or "none"
    print(f"| `{path}` | {graph_side} | {Path(declared.get(path, '')).stem or '**none**'} |")

print("\n## Q5. The most connected nodes (degree, code only)")
degree = collections.Counter()
for link in links:
    degree[link["source"]] += 1
    degree[link["target"]] += 1
code = [(count, node_id) for node_id, count in degree.items() if nodes[node_id].get("file_type") == "code"]
for count, node_id in sorted(code, reverse=True)[:10]:
    print(f"- {count:3d}  {nodes[node_id].get('label')}  ({file_of(node_id)})")
