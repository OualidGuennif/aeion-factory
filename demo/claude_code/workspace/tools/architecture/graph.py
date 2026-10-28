#!/usr/bin/env python3
# Spec: knowledge/operations/architecture-maintenance.md
"""Use pinned Graphify extractors on the explicit current corpus, including Markdown."""
import hashlib
import importlib.metadata
import json
from pathlib import Path
import sys


def main():
    from graphify.extract import extract
    from graphify.build import build
    from graphify.export import to_json

    root, out, manifest_file = map(Path, sys.argv[1:])
    manifest = json.loads(manifest_file.read_text())
    paths = [root / item["path"] for item in manifest]
    extraction = extract(paths, cache_root=out, root=root, parallel=False)
    sources = {str(node.get("source_file", "")) for node in extraction["nodes"]}
    required = [item["path"] for item in manifest if item["required"]]
    missing = sorted(set(required) - sources)
    if missing:
        raise ValueError(f"Graphify coverage missing {len(missing)} required files: {', '.join(missing[:8])}")
    graph = build([extraction], directed=True, dedup=False, root=root)
    if not graph or not to_json(graph, {}, str(out / "graph.json"), force=True):
        raise ValueError("Graphify did not produce a persistent graph")
    coverage = {"mode": "native structural code, Markdown and config; no LLM inference",
                "graphify_version": importlib.metadata.version("graphifyy"),
                "required_files": len(required), "extracted_files": sorted(sources & {item["path"] for item in manifest}),
                "inventory_only": sorted({item["path"] for item in manifest} - sources),
                "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "missing": missing}
    (out / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    (out / "GRAPH_REPORT.md").write_text("# Æion Factory Graphify structural report\n\n"
        f"{coverage['nodes']} nodes, {coverage['edges']} edges; {len(required)} required source/docs files covered.\n\n"
        "Native Markdown headings, frontmatter and links are included. Inferred edges retain upstream confidence.\n"
        "This is a structural graph, not complete semantic understanding. See coverage.json for inventory-only paths.\n")


if __name__ == "__main__":
    main()
