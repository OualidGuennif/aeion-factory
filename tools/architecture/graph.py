#!/usr/bin/env python3
# Spec: knowledge/operations/architecture-maintenance.md
"""Use pinned Graphify extractors on the explicit current corpus, including Markdown."""
import hashlib
import importlib.metadata
import json
import posixpath
from pathlib import Path
import sys


def spec_source_edges(nodes):
    """The spec -> file edges a doc's frontmatter `sources` declares, and the resources that name no
    file in the graph. Graphify keeps the frontmatter on the page node but links only the code names
    written in the body, so the factory's own spec <-> code contract would otherwise be missing."""
    files = {}
    for node_id, data in nodes:
        source = str(data.get("source_file", ""))
        label, name = str(data.get("label", "")), posixpath.basename(source)
        # Graphify labels a file by its name, or by a longer suffix when two files share it (pages/vote.ts).
        if source and (label == name or label.endswith("/" + name)):
            files.setdefault(source, node_id)
    edges, unresolved = [], []
    for node_id, data in nodes:
        sources = (data.get("frontmatter") or {}).get("sources") if data.get("node_kind") == "page" else None
        if not isinstance(sources, list):
            continue
        doc = str(data["source_file"])
        for item in sources:
            resource = item.get("resource") if isinstance(item, dict) else None
            # Only a relative path names a file in this corpus; a URL is evidence elsewhere.
            if not isinstance(resource, str) or "://" in resource or resource.startswith("/"):
                continue
            path = posixpath.normpath(posixpath.join(posixpath.dirname(doc), resource))
            if path in files:
                edges.append((node_id, files[path], {"relation": "specifies", "confidence": "EXTRACTED",
                                                     "confidence_score": 1.0, "_origin": "frontmatter",
                                                     "source_file": doc, "source_location": "L1", "weight": 1.0}))
            else:
                unresolved.append(f"{doc}: {resource}")
    return edges, unresolved


def main():
    from graphify.extract import extract
    from graphify.build import build
    from graphify.export import to_json

    # Graphify makes source paths relative to an absolute root only.
    root, out, manifest_file = (Path(arg).resolve() for arg in sys.argv[1:])
    manifest = json.loads(manifest_file.read_text())
    paths = [root / item["path"] for item in manifest]
    extraction = extract(paths, cache_root=out, root=root, parallel=False)
    sources = {str(node.get("source_file", "")) for node in extraction["nodes"]}
    required = [item["path"] for item in manifest if item["required"]]
    missing = sorted(set(required) - sources)
    if missing:
        raise ValueError(f"Graphify coverage missing {len(missing)} required files: {', '.join(missing[:8])}")
    graph = build([extraction], directed=True, dedup=False, root=root)
    spec_edges, unresolved = spec_source_edges(list(graph.nodes(data=True)))
    for source, target, data in spec_edges:
        graph.add_edge(source, target, **data)
    if not graph or not to_json(graph, {}, str(out / "graph.json"), force=True):
        raise ValueError("Graphify did not produce a persistent graph")
    coverage = {"mode": "native structural code, Markdown and config; no LLM inference",
                "graphify_version": importlib.metadata.version("graphifyy"),
                "required_files": len(required), "extracted_files": sorted(sources & {item["path"] for item in manifest}),
                "inventory_only": sorted({item["path"] for item in manifest} - sources),
                "nodes": graph.number_of_nodes(), "edges": graph.number_of_edges(), "missing": missing,
                "spec_source_edges": len(spec_edges), "unresolved_spec_sources": unresolved}
    (out / "coverage.json").write_text(json.dumps(coverage, indent=2) + "\n")
    (out / "GRAPH_REPORT.md").write_text("# Æion Factory Graphify structural report\n\n"
        f"{coverage['nodes']} nodes, {coverage['edges']} edges; {len(required)} required source/docs files covered.\n\n"
        "Native Markdown headings, frontmatter and links are included; each spec's frontmatter `sources` adds a\n"
        f"`specifies` edge ({len(spec_edges)} here, {len(unresolved)} unresolved). Inferred edges retain upstream confidence.\n"
        "This is a structural graph, not complete semantic understanding. See coverage.json for inventory-only paths.\n")


if __name__ == "__main__":
    main()
