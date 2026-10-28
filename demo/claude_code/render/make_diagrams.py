#!/usr/bin/env python3
"""Write the Idea Board gallery's Archify inputs to diagrams/<name>.json, one small diagram per question."""
import json
from pathlib import Path

OUT = Path(__file__).parent / "diagrams"


def meta(title, name, **extra):
    return {"title": title, "output": f"diagrams/{name}.html", "animation": "trace", "quality_profile": "showcase", **extra}


def box(id, type, label, sublabel, pos, tag=None, size=(132, 60)):
    component = {"id": id, "type": type, "label": label, "sublabel": sublabel, "pos": list(pos), "size": list(size)}
    if tag:
        component["tag"] = tag
    return component


def link(source, target, label=None, **extra):
    connection = {"from": source, "to": target, **extra}
    if label:
        connection["label"] = label
    return connection


def card(dot, title, *items):
    return {"dot": dot, "title": title, "items": list(items)}


DIAGRAMS = {}

DIAGRAMS["system-overview"] = ("architecture", {
    "schema_version": 1, "diagram_type": "architecture",
    "meta": meta("Idea Board: system overview", "system-overview", visual_preset="blueprint"),
    "components": [
        box("browser", "external", "Browser", "HTML first", (40, 300)),
        box("islands", "frontend", "Islands", "NewIdeaForm, VoteButton", (40, 470)),
        box("fresh", "backend", "Fresh server", "routes, SSR, csrf()", (260, 300), "serve.ts"),
        box("pages", "backend", "Page handlers", "home.tsx, vote.ts", (480, 180)),
        box("api", "backend", "Hono API", "/api/* catch-all", (480, 420)),
        box("domain", "security", "Domain", "validate, parse filters", (700, 300)),
        box("store", "backend", "Idea store", "store/ideas.ts", (920, 300)),
        box("kv", "database", "Deno KV", "SQLite file, KV_PATH", (1140, 300)),
    ],
    "boundaries": [
        {"kind": "region", "label": "Deno process", "wraps": ["fresh", "pages", "api", "domain", "store"], "pad": 20},
    ],
    "connections": [
        link("browser", "fresh", "GET / and form posts", variant="emphasis"),
        link("islands", "fresh", "fetch /api/*", variant="dashed"),
        link("fresh", "pages", "/, /ideas/:id/vote", route="orthogonal-v"),
        link("fresh", "api", "/api/*", route="orthogonal-v"),
        link("pages", "domain", "parse"),
        link("api", "domain", "validate"),
        link("domain", "store", "valid draft", variant="emphasis"),
        link("store", "kv", "atomic commit", variant="emphasis"),
    ],
    "cards": [
        card("cyan", "One process", "Fresh serves pages and mounts Hono under /api", "Both share one lazily opened store"),
        card("emerald", "HTML first", "Forms post without JavaScript", "Islands only enhance: fetch instead of reload"),
        card("rose", "One rule set", "The page and the API call the same validation", "They differ only in what they do with a refusal"),
    ],
})

DIAGRAMS["docker-deployment"] = ("architecture", {
    "schema_version": 1, "diagram_type": "architecture",
    "meta": meta("Idea Board: Docker deployment", "docker-deployment", visual_preset="blueprint"),
    "components": [
        box("operator", "external", "Operator", "docker compose", (40, 160)),
        box("visitor", "external", "Visitor", "browser", (40, 420)),
        box("image", "cloud", "idea-board:local", "deno 2.9.8, frozen lock", (280, 160), "build"),
        box("port", "security", "Host port", "8000:8000", (280, 420)),
        box("web", "backend", "web container", "uid 1993 (deno)", (540, 300), "least privilege"),
        box("probe", "security", "Health check", "deno eval fetch", (800, 160), "every 5 s"),
        box("volume", "database", "ideas-data", "/data/ideas.sqlite3", (800, 420), "named volume"),
    ],
    "boundaries": [
        {"kind": "region", "label": "Docker host", "wraps": ["image", "port", "web", "probe", "volume"], "pad": 22},
        {"kind": "security-group", "label": "container: cap_drop ALL, no-new-privileges", "wraps": ["web", "probe"], "pad": 14},
    ],
    "connections": [
        link("operator", "image", "up --build", variant="emphasis"),
        link("image", "web", "runs", route="orthogonal-v"),
        link("visitor", "port", "HTTP", variant="emphasis"),
        link("port", "web", "published", route="orthogonal-v"),
        link("probe", "web", "GET /api/health", variant="dashed", route="orthogonal-v"),
        link("web", "volume", "KV_PATH", variant="emphasis", route="orthogonal-v"),
    ],
    "cards": [
        card("cyan", "Pinned and locked", "denoland/deno:2.9.8, the latest stable", "deno install --frozen stops a drifted lock"),
        card("rose", "Least privilege", "Non-root user, no capabilities", "Deno may write only /data and download nothing"),
        card("emerald", "Data survives", "down keeps the volume; down -v deletes it"),
    ],
})


def use_case(name, title, actor, actor_sub, cases, partner=None, notes=()):
    components = [box("actor", "external", actor, actor_sub, (40, 280))]
    for index, (label, sub) in enumerate(cases):
        components.append(box(f"uc{index}", "frontend", label, sub, (340, 60 + index * 120), size=(190, 60)))
    connections = [link("actor", f"uc{index}") for index in range(len(cases))]
    if partner:
        components.append(box("partner", partner[2], partner[0], partner[1], (700, 280)))
        connections += [link(f"uc{index}", "partner", variant="dashed") for index in partner[3]]
    return ("architecture", {
        "schema_version": 1, "diagram_type": "architecture",
        "meta": meta(title, name, visual_preset="blueprint"),
        "components": components,
        "boundaries": [{"kind": "region", "label": "Idea Board", "wraps": [f"uc{i}" for i in range(len(cases))], "pad": 20}],
        "connections": connections,
        "cards": [card("cyan", "How to read it", "Archify has no use-case type: the actor is an external component",
                       "Use cases are components inside the system boundary"), *notes],
    })


DIAGRAMS["use-cases-visitor"] = use_case(
    "use-cases-visitor", "Use cases: Visitor", "Visitor", "no account", [
        ("Browse ideas", "newest first"), ("Sort by votes", "/?sort=votes"),
        ("Filter by tag", "/?tag=ui"), ("Search text", "/?q=dark")],
    notes=[card("emerald", "Without JavaScript", "Every use case is a plain link or GET form", "Filters and sort are kept together")])

DIAGRAMS["use-cases-contributor"] = use_case(
    "use-cases-contributor", "Use cases: Contributor", "Contributor", "writes and votes", [
        ("Propose an idea", "title, description, tags"), ("Fix a refused field", "message by the field"),
        ("Vote for an idea", "+1, in place")],
    partner=("Deno KV", "atomic commits", "database", [0, 2]),
    notes=[card("rose", "Refusals", "400 with field and reason; nothing is written", "A busy vote returns 503 after 10 attempts")])

DIAGRAMS["use-cases-operator"] = use_case(
    "use-cases-operator", "Use cases: Operator", "Operator", "runs the board", [
        ("Start the board", "docker compose up"), ("Check health", "compose ps: healthy"),
        ("Restart, keep data", "down, then up"), ("Reset the data", "down -v")],
    partner=("Docker", "compose, volume", "cloud", [0, 1, 2, 3]),
    notes=[card("emerald", "Checked", "container_check.sh runs all four", "Each check fails rather than passing for the wrong reason")])


def sequence(name, title, participants, segments, messages, notes):
    # Messages are 32 px apart from y=160; segments name index ranges; each non-external lifeline is active
    # from its first to its last message.
    ys = [160 + 32 * index for index in range(len(messages))]
    kinds = {id: type for id, type, _, _ in participants}
    activations = []
    for id, type, _, _ in participants:
        touched = [ys[n] for n, (f, t, _, _) in enumerate(messages) if id in (f, t)]
        if type != "external" and touched:
            activations.append({"participant": id, "from": min(touched) - 6, "to": max(touched) + 6, "type": kinds[id]})
    return ("sequence", {
        "schema_version": 1, "diagram_type": "sequence",
        "meta": meta(title, name, column_fit="spread"),
        "participants": [{"id": i, "type": t, "label": l, "sublabel": s} for i, t, l, s in participants],
        "segments": [{"from": ys[a] - 12, "to": ys[b] + 12, "label": l} for a, b, l in segments],
        "messages": [{"id": f"m{n}", "from": f, "to": t, "y": ys[n], "label": l, "variant": v}
                     for n, (f, t, l, v) in enumerate(messages)],
        "activations": activations,
        "cards": notes,
    })


DIAGRAMS["sequence-page-load"] = sequence(
    "sequence-page-load", "Sequence: page load (server-side rendering)",
    [("browser", "external", "Browser", "visitor"), ("fresh", "backend", "Fresh", "route /"),
     ("home", "backend", "Home handler", "GET"), ("store", "backend", "Idea store", "list()"),
     ("kv", "database", "Deno KV", "index + ideas")],
    [(0, 1, "Request"), (2, 7, "Read"), (8, 9, "Render")],
    [("browser", "fresh", "GET /?sort=votes", "emphasis"), ("fresh", "home", "GET(ctx): read sort, filters", "default"),
     ("home", "store", "list({limit 20, sort})", "emphasis"),
     ("store", "kv", "list ideas_by_votes, reverse", "default"), ("kv", "store", "ids", "return"),
     ("store", "kv", "getMany, 10 keys a call", "default"), ("kv", "store", "ideas", "return"),
     ("store", "home", "matches: includes, sort, slice", "return"), ("home", "fresh", "page(data)", "return"),
     ("fresh", "browser", "HTML, then islands hydrate", "return")],
    [card("emerald", "Readable before JavaScript", "The full list arrives as HTML", "Islands hydrate afterwards and only enhance"),
     card("cyan", "Index reads", "getMany reads at most 10 keys per call", "The handler batches the ids")])

DIAGRAMS["sequence-create-idea"] = sequence(
    "sequence-create-idea", "Sequence: create an idea",
    [("user", "external", "Contributor", "browser"), ("island", "frontend", "NewIdeaForm", "island"),
     ("api", "backend", "Hono API", "POST /api/ideas"), ("domain", "security", "Domain", "validateNewIdea"),
     ("store", "backend", "Idea store", "create()"), ("kv", "database", "Deno KV", "one commit")],
    [(0, 1, "Submit"), (2, 3, "Validate"), (4, 7, "Store + answer")],
    [("user", "island", "submit form", "default"), ("island", "api", "POST JSON (bodyLimit)", "emphasis"),
     ("api", "domain", "validateNewIdea(body)", "security"),
     ("domain", "api", "ok, or field + reason", "return"),
     ("api", "store", "create(draft)", "emphasis"),
     ("store", "kv", "check + set idea, votes, tags", "emphasis"), ("kv", "store", "ok", "return"),
     ("api", "island", "201 {idea} (or 400)", "return"), ("island", "user", "reset, show list", "return")],
    [card("rose", "A refusal writes nothing", "400 names the field and the reason", "The island shows it under the field"),
     card("emerald", "All or nothing", "The idea, its votes key and its tag keys land in one atomic commit")])

DIAGRAMS["sequence-vote"] = sequence(
    "sequence-vote", "Sequence: vote (optimistic transaction with retry)",
    [("user", "external", "Visitor", "browser"), ("button", "frontend", "VoteButton", "island"),
     ("api", "backend", "Hono API", "POST …/vote"), ("store", "backend", "Idea store", "vote(id)"),
     ("kv", "database", "Deno KV", "versionstamps")],
    [(0, 2, "Request"), (3, 8, "Optimistic loop, up to 10"), (9, 10, "Answer")],
    [("user", "button", "click Vote", "default"), ("button", "api", "POST /api/ideas/:id/vote", "emphasis"),
     ("api", "store", "vote(id)", "emphasis"),
     ("store", "kv", "get idea (versionstamp)", "default"), ("kv", "store", "idea, v1", "return"),
     ("store", "kv", "check v1, set votes+1, move index", "emphasis"),
     ("kv", "store", "conflict: someone voted", "return"),
     ("store", "kv", "after 0..2^n ms: get, commit", "emphasis"), ("kv", "store", "ok", "return"),
     ("api", "button", "200 {idea} (503 if busy)", "return"), ("button", "user", "count +1, aria-live", "return")],
    [card("orange", "Why the jitter", "No backoff: 15 of 25 concurrent votes needed more than 10 attempts",
          "With 0..2^n ms jitter: at most 8"),
     card("emerald", "Nothing lost", "30 concurrent votes give exactly 30")])

DIAGRAMS["sequence-filter-search"] = sequence(
    "sequence-filter-search", "Sequence: filter by tag and search",
    [("browser", "external", "Browser", "GET form"), ("home", "backend", "Home handler", "lenient"),
     ("filters", "security", "parseFilters", "tag, q"), ("store", "backend", "Idea store", "filtered()"),
     ("kv", "database", "Deno KV", "ideas_by_tag")],
    [(0, 2, "Parse"), (3, 7, "Read at most 500"), (8, 9, "Render")],
    [("browser", "home", "GET /?tag=ui&q=dark&sort=votes", "emphasis"),
     ("home", "filters", "each filter alone", "security"), ("filters", "home", "valid ones kept", "return"),
     ("home", "store", "list({tag, q, sort})", "emphasis"),
     ("store", "kv", "list ideas_by_tag/ui, 500", "default"), ("kv", "store", "ids", "return"),
     ("store", "kv", "getMany in tens", "default"), ("kv", "store", "candidates", "return"),
     ("store", "home", "Idea[]", "return"), ("home", "browser", "HTML, filters kept in every link", "return")],
    [card("rose", "Never a regex", "q is a plain substring: '.*' matches only those two characters"),
     card("cyan", "Bounded", "A filtered read looks at the 500 newest candidates, then sorts them"),
     card("emerald", "Page vs API", "The page drops an invalid filter; the API answers 400")])

DIAGRAMS["sequence-health"] = sequence(
    "sequence-health", "Sequence: health check in the container",
    [("operator", "external", "Operator", "compose ps"), ("docker", "cloud", "Docker engine", "healthcheck"),
     ("probe", "security", "deno eval", "inside the container"), ("api", "backend", "Hono API", "/api/health")],
    [(0, 1, "Probe"), (2, 3, "Answer"), (4, 5, "Report")],
    [("docker", "probe", "every 5 s, timeout 3 s", "default"),
     ("probe", "api", "fetch 127.0.0.1:8000/api/health", "emphasis"),
     ("api", "probe", "200 {status: ok, version}", "return"),
     ("probe", "docker", "exit 0; 5 failures: unhealthy", "return"),
     ("operator", "docker", "docker compose ps", "default"), ("docker", "operator", "healthy", "return")],
    [card("emerald", "No curl in the image", "The probe is the app's own runtime", "Healthy 6 s after up")])

DIAGRAMS["idea-lifecycle"] = ("lifecycle", {
    "schema_version": 3, "diagram_type": "lifecycle",
    "meta": meta("Lifecycle of an idea", "idea-lifecycle"),
    "mainPath": ["draft", "validating", "stored", "listed"],
    "states": [
        {"id": "draft", "type": "start", "label": "Draft", "sublabel": "form or JSON", "tag": "entry", "step": "01"},
        {"id": "validating", "type": "decision", "label": "Validating", "sublabel": "validateNewIdea", "tag": "check", "step": "02"},
        {"id": "stored", "type": "active", "label": "Stored", "sublabel": "votes 0, indexed", "tag": "KV", "step": "03"},
        {"id": "listed", "type": "success", "label": "Listed", "sublabel": "sort, tag, search", "tag": "visible", "step": "04"},
        {"id": "refused", "type": "failure", "label": "Refused", "sublabel": "400 field + reason", "tag": "nothing written"},
        {"id": "voting", "type": "active", "label": "Vote in flight", "sublabel": "optimistic commit", "tag": "retry ≤ 10"},
        {"id": "busy", "type": "waiting", "label": "Busy", "sublabel": "503 after 10 tries", "tag": "rare"},
    ],
    "transitions": [
        {"id": "t1", "from": "draft", "to": "validating", "label": "submit"},
        {"id": "t2", "from": "validating", "to": "stored", "label": "valid"},
        {"id": "t3", "from": "stored", "to": "listed", "label": "GET /"},
        {"id": "t4", "from": "validating", "to": "refused", "label": "invalid", "variant": "security"},
        {"id": "t5", "from": "refused", "to": "draft", "label": "fix the field", "variant": "dashed"},
        {"id": "t6", "from": "listed", "to": "voting", "label": "vote"},
        {"id": "t7", "from": "voting", "to": "listed", "label": "votes + 1"},
        {"id": "t8", "from": "voting", "to": "busy", "label": "10 conflicts", "variant": "security"},
        {"id": "t9", "from": "busy", "to": "voting", "label": "vote again", "variant": "dashed"},
    ],
    "cards": [
        card("emerald", "No end state", "Ideas are never edited or deleted in this version"),
        card("rose", "Refusals write nothing", "A refused draft never reaches KV"),
    ],
})

DIAGRAMS["kv-key-model"] = ("erd", {
    "schema_version": 1, "diagram_type": "erd",
    "meta": meta("Deno KV key model", "kv-key-model"),
    "layout": {"mode": "grid", "gapY": 38, "gapX": 72},
    "entities": [
        {"id": "ideas", "label": "[\"ideas\", id] → Idea", "tag": "primary", "row": 0, "col": 1, "width": 270, "attributes": [
            {"name": "id", "type": "ULID (monotonic)", "key": "pk"}, {"name": "title", "type": "string 3–80"},
            {"name": "description", "type": "string ≤ 500"}, {"name": "tags", "type": "string[] ≤ 5"},
            {"name": "votes", "type": "number"}, {"name": "createdAt", "type": "ISO date"}]},
        {"id": "by_votes", "label": "[\"ideas_by_votes\", votes, id] → id", "tag": "index", "row": 0, "col": 0, "width": 300, "attributes": [
            {"name": "votes", "type": "number", "key": "pk"},
            {"name": "id", "type": "ULID", "key": "fk", "references": "ideas.id"}]},
        {"id": "by_tag", "label": "[\"ideas_by_tag\", tag, id] → id", "tag": "index", "row": 1, "col": 0, "width": 290, "attributes": [
            {"name": "tag", "type": "[a-z0-9-]", "key": "pk"},
            {"name": "id", "type": "ULID", "key": "fk", "references": "ideas.id"}]},
    ],
    "relationships": [
        {"id": "votes_idea", "from": "by_votes", "to": "ideas", "label": "one per idea", "fromCardinality": "one", "toCardinality": "one"},
        {"id": "tag_idea", "from": "by_tag", "to": "ideas", "label": "one per tag", "fromCardinality": "many", "toCardinality": "one"},
    ],
    "cards": [
        card("cyan", "Keys are the indexes", "Listing a prefix in reverse gives newest or most voted first",
             "A ULID orders ties newest first"),
        card("emerald", "Moved together", "A vote deletes the old votes key and writes the new one in the same commit"),
    ],
})

DIAGRAMS["request-dataflow"] = ("dataflow", {
    "schema_version": 1, "diagram_type": "dataflow",
    "meta": meta("Request data flow: from a form to KV", "request-dataflow", viewBox=[1080, 620], visual_preset="signal-flow"),
    "stages": [{"label": "Input"}, {"label": "Parse"}, {"label": "Validate"}, {"label": "Store"}, {"label": "Answer"}],
    "nodes": [
        {"id": "form", "type": "frontend", "label": "HTML form", "sublabel": "urlencoded", "stage": 0, "row": 0, "tag": "no JS"},
        {"id": "json", "type": "frontend", "label": "Island JSON", "sublabel": "fetch", "stage": 0, "row": 2, "tag": "enhanced"},
        {"id": "parse_form", "type": "backend", "label": "parseIdeaForm", "sublabel": "split tags", "stage": 1, "row": 0},
        {"id": "parse_json", "type": "backend", "label": "Hono body", "sublabel": "bodyLimit", "stage": 1, "row": 2},
        {"id": "validate", "type": "security", "label": "validateNewIdea", "sublabel": "one rule set", "stage": 2, "row": 1, "tag": "shared"},
        {"id": "kv", "type": "database", "label": "Deno KV", "sublabel": "atomic commit", "stage": 3, "row": 1},
        {"id": "page", "type": "frontend", "label": "303 or 400 page", "sublabel": "message by field", "stage": 4, "row": 0},
        {"id": "api_out", "type": "frontend", "label": "201 or 400 JSON", "sublabel": "{error, field, reason}", "stage": 4, "row": 2},
    ],
    "flows": [
        {"from": "form", "to": "parse_form", "label": "FormData", "variant": "emphasis", "route": "straight"},
        {"from": "json", "to": "parse_json", "label": "JSON", "variant": "emphasis", "route": "straight"},
        {"from": "parse_form", "to": "validate", "label": "values", "variant": "emphasis"},
        {"from": "parse_json", "to": "validate", "label": "body", "variant": "emphasis"},
        {"from": "validate", "to": "kv", "label": "valid draft", "classification": "Idea", "variant": "emphasis", "route": "straight"},
        {"from": "kv", "to": "page", "label": "redirect"},
        {"from": "kv", "to": "api_out", "label": "idea"},
    ],
    "cards": [
        card("rose", "One rule set", "Both entry points meet at validateNewIdea", "A refusal skips KV and answers at once"),
        card("cyan", "Same contract", "The page message and the API reason come from one list"),
    ],
})

DIAGRAMS["aeion-round"] = ("workflow", {
    # Schema 2 lays columns out by content; fixed-v1 columns overlap at six columns.
    "schema_version": 2, "diagram_type": "workflow",
    "meta": meta("The Æion round that built each feature", "aeion-round"),
    "lanes": [
        {"id": "owner", "label": "Owner"}, {"id": "agent", "label": "Agent"},
        {"id": "checks", "label": "Checks and hooks"}, {"id": "repo", "label": "Parent repository"},
        {"id": "friction", "label": "Friction", "variant": "exception"},
    ],
    "phases": [
        {"id": "think", "label": "Plan + spec", "fromCol": 0, "toCol": 1},
        {"id": "make", "label": "Tests + build", "fromCol": 2, "toCol": 3, "variant": "emphasis"},
        {"id": "prove", "label": "Prove + record", "fromCol": 4, "toCol": 5, "variant": "dashed"},
    ],
    "mainPath": ["brief", "plan", "tests", "build", "batteries", "journal", "approve"],
    "nodes": [
        {"id": "brief", "lane": "owner", "col": 0, "type": "external", "label": "Brief", "sublabel": "demo/plan/0N"},
        {"id": "plan", "lane": "agent", "col": 1, "type": "frontend", "label": "Plan + spec", "sublabel": "skills plan, spec"},
        {"id": "tests", "lane": "agent", "col": 2, "type": "backend", "label": "Tests", "sublabel": "first"},
        {"id": "build", "lane": "agent", "col": 3, "type": "backend", "label": "Build slices", "sublabel": "skill build"},
        {"id": "batteries", "lane": "checks", "col": 4, "type": "security", "label": "Batteries", "sublabel": "fmt, lint, test, smoke"},
        {"id": "journal", "lane": "repo", "col": 5, "type": "database", "label": "Journal + commit", "sublabel": "develop, local"},
        {"id": "approve", "lane": "owner", "col": 5, "type": "external", "label": "Visual yes", "sublabel": "screenshots"},
        {"id": "hook", "lane": "checks", "col": 3, "type": "security", "label": "Edit hooks", "sublabel": "guard, doc-links"},
        {"id": "fb", "lane": "friction", "col": 4, "type": "messagebus", "label": "FB-0NN", "sublabel": "feedback_for_aeion"},
    ],
    "edges": [
        {"from": "brief", "to": "plan"}, {"from": "plan", "to": "tests"},
        {"from": "tests", "to": "build"}, {"from": "build", "to": "batteries"}, {"from": "batteries", "to": "journal"},
        {"from": "journal", "to": "approve"},
        {"from": "build", "to": "hook", "label": "every edit", "variant": "dashed"},
        {"from": "hook", "to": "fb", "label": "refusal", "variant": "dashed", "role": "error"},
    ],
    "cards": [
        card("emerald", "Seven rounds", "Scaffold, API, page, votes, tags + search, Docker, this gallery"),
        card("rose", "Friction is output", "Each blocked step became a feedback file for the factory"),
    ],
})


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for name, (kind, diagram) in DIAGRAMS.items():
        (OUT / f"{name}.json").write_text(json.dumps(diagram, indent=2, ensure_ascii=False) + "\n")
        print(kind, name)
