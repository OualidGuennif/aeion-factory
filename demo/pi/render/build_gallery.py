#!/usr/bin/env python3
"""Build render/index.html: one self-contained gallery with every diagram inlined.

The standalone diagram files need a readable file:// path (macOS protects the Desktop) and are
blocked in iframes from disk, so the atlas inlines each diagram as JSON, sets it as an iframe
srcdoc, and offers a full-window view of the same markup. No network, no server, no file access
beyond this one HTML. Regenerate after changing a diagram: python3 build_gallery.py (the HTML is generated, not tracked)
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAGRAMS = HERE / "diagrams"

GROUPS = [
    ("System", [
        ("system-overview", "architecture", "Idea Board as one Deno process",
         "Where does browser behaviour meet server authority?"),
        ("deployment", "architecture · deployment", "Idea Board in Docker",
         "What survives a container restart?"),
    ]),
    ("Sequences", [
        ("seq-page-load", "sequence", "Page load, server-rendered",
         "How is GET / rendered, and what is left for the browser?"),
        ("seq-create", "sequence", "Create an idea: island to KV",
         "What happens between a click and a stored idea?"),
        ("seq-vote", "sequence", "A vote: optimistic, queued, retried",
         "How do concurrent votes avoid lost updates?"),
        ("seq-filter", "sequence", "Filters: tag index first, text within a window",
         "Which ideas can a search match, and at what cost?"),
        ("seq-health", "sequence", "Health check inside the container",
         "What does the container health check actually prove?"),
    ]),
    ("Use cases", [
        ("use-case-visitor", "architecture · use-case notation", "Visitor: read the board",
         "What can a visitor do without an account or JavaScript?"),
        ("use-case-contributor", "architecture · use-case notation", "Contributor: create and vote",
         "Which mutations exist, and what does a refusal look like?"),
        ("use-case-operator", "architecture · use-case notation", "Operator: run and verify",
         "How is the board started, checked and kept?"),
    ]),
    ("Models and delivery", [
        ("idea-lifecycle", "lifecycle", "Idea lifecycle",
         "Which states, which refusals, and what can never change?"),
        ("kv-model", "tree", "Idea Board KV key model",
         "How does KV support order, votes and tags?"),
        ("request-dataflow", "dataflow", "Request data through Idea Board",
         "Where does untrusted input become a trusted idea?"),
        ("aeion-round", "workflow", "The Æion round that built Idea Board",
         "Which steps prove a change before it is committed?"),
    ]),
]

STYLE = """
:root{color-scheme:light;--paper:#f7f4ec;--ink:#1d2f2a;--muted:#5a6a63;--line:#d9ded4;--accent:#8a3f1d}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.6 system-ui,sans-serif}
main{max-width:1320px;margin:auto;padding:56px 24px}
header{max-width:900px;margin-bottom:48px}
.eyebrow,.kind{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:var(--accent)}
h1{font:clamp(38px,6vw,68px)/1.06 Georgia,serif;letter-spacing:-.035em;margin:14px 0 24px}
h2{font:32px/1.2 Georgia,serif;margin:48px 0 20px}
h3{font:25px/1.2 Georgia,serif;margin:10px 0}
p{color:var(--muted)}
button{font:inherit;color:var(--ink);background:#fffdf8;border:1px solid var(--line);border-radius:999px;padding:6px 14px;cursor:pointer}
button:hover{border-color:var(--accent)}
a{color:var(--ink);text-underline-offset:4px}
a:focus-visible,button:focus-visible{outline:3px solid var(--accent);outline-offset:4px}
.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}
article{border:1px solid var(--line);border-radius:14px;overflow:hidden;background:#fffdf8}
.preview{position:relative;height:245px;overflow:hidden;background:#eef1ea;border-bottom:1px solid var(--line)}
.preview iframe{width:1200px;height:500px;transform:scale(.49);transform-origin:top left;border:0;pointer-events:none}
.preview .empty{position:absolute;inset:0;display:grid;place-items:center;color:var(--muted);font-size:14px}
.preview[data-ready="true"] .empty{display:none}
.copy{padding:22px 24px 28px}
.copy p{margin:10px 0 20px}
.copy .kind{margin:0}
.actions{display:flex;align-items:center;gap:14px}
.source{font-size:13px;color:var(--muted);margin-left:auto}
footer{border-top:1px solid var(--line);margin-top:56px;padding-top:22px;color:var(--muted)}
#viewer{position:fixed;inset:0;background:#0d1512;display:none;z-index:10}
#viewer[data-open="true"]{display:block}
#viewer iframe{position:absolute;inset:56px 16px 16px;width:calc(100% - 32px);height:calc(100% - 72px);border:1px solid #2a3a34;border-radius:10px;background:#fff}
#viewer .bar{display:flex;align-items:center;gap:16px;padding:10px 18px;color:#e8efe9}
#viewer .bar strong{font:20px/1.2 Georgia,serif;font-weight:600}
#viewer .bar button{background:#16211d;color:#e8efe9;border-color:#33453e}
#viewer .bar button.close{margin-left:auto}
@media(max-width:750px){main{padding:32px 18px}.grid{grid-template-columns:1fr}.preview{height:180px}.preview iframe{transform:scale(.31)}}
"""

SCRIPT = """
const data = {};
const titles = {};
const order = [];
for (const node of document.querySelectorAll('script[type="application/json"][data-diagram]')) {
  data[node.dataset.diagram] = JSON.parse(node.textContent);
  order.push(node.dataset.diagram);
}
for (const button of document.querySelectorAll('button[data-open]')) {
  titles[button.dataset.open] = button.dataset.title;
}
const frames = document.querySelectorAll('iframe[data-diagram]');
const load = (frame) => {
  if (frame.dataset.loaded === 'true') return;
  frame.dataset.loaded = 'true';
  const card = frame.closest('.preview');
  frame.addEventListener('load', () => { card.dataset.ready = 'true'; }, { once: true });
  frame.srcdoc = data[frame.dataset.diagram];
};
const watcher = new IntersectionObserver((entries) => {
  for (const entry of entries) if (entry.isIntersecting) { load(entry.target); watcher.unobserve(entry.target); }
}, { rootMargin: '600px' });
for (const frame of frames) watcher.observe(frame);

const viewer = document.getElementById('viewer');
const viewerFrame = viewer.querySelector('iframe');
const viewerTitle = viewer.querySelector('strong');
let current = 0;
const show = (index) => {
  current = (index + order.length) % order.length;
  const name = order[current];
  viewerTitle.textContent = titles[name] || name;
  viewerFrame.srcdoc = data[name];
  viewer.dataset.open = 'true';
  document.body.style.overflow = 'hidden';
};
const close = () => {
  viewer.dataset.open = 'false';
  viewerFrame.removeAttribute('srcdoc');
  document.body.style.overflow = '';
  document.querySelector('button[data-open="' + order[current] + '"]')?.focus();
};
for (const button of document.querySelectorAll('button[data-open]')) {
  button.addEventListener('click', () => show(order.indexOf(button.dataset.open)));
}
viewer.querySelector('button.close').addEventListener('click', close);
viewer.querySelector('button.prev').addEventListener('click', () => show(current - 1));
viewer.querySelector('button.next').addEventListener('click', () => show(current + 1));
document.addEventListener('keydown', (event) => {
  if (viewer.dataset.open !== 'true') return;
  if (event.key === 'Escape') close();
  if (event.key === 'ArrowLeft') show(current - 1);
  if (event.key === 'ArrowRight') show(current + 1);
});
"""


def main():
    parts = []
    for name, kind, title, question in (entry for _, rows in GROUPS for entry in rows):
        source = DIAGRAMS / f"{name}.html"
        html = source.read_text(encoding="utf-8")
        payload = json.dumps(html).replace("</", "<\\/")
        parts.append(f'<script type="application/json" data-diagram="{name}">{payload}</script>')

    sections = []
    for group, rows in GROUPS:
        cards = []
        for name, kind, title, question in rows:
            cards.append(
                f'<article><div class="preview"><iframe data-diagram="{name}" '
                f'title="{title}" loading="lazy"></iframe>'
                f'<div class="empty" aria-hidden="true">Loading preview…</div></div>'
                f'<div class="copy"><p class="kind">{kind}</p><h3>{title}</h3><p>{question}</p>'
                f'<div class="actions"><button data-open="{name}" data-title="{title}">Open full size</button>'
                f'<a href="diagrams/{name}.html">standalone file</a>'
                f'<a class="source" href="diagrams/{name}.json">JSON</a></div></div></article>'
            )
        sections.append(f'<section><h2>{group}</h2><div class="grid">{"".join(cards)}</div></section>')

    total = sum(len(part) for part in parts)
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Idea Board — architecture atlas</title>
<style>{STYLE}</style>
</head>
<body>
<main>
<header>
<p class="eyebrow">Pi demo · Round 07 · One file, no server</p>
<h1>A small board.<br>A clear architecture.</h1>
<p>Fourteen focused views of the Idea Board, inlined in this page: every preview and the
full-size view work from a single <code>file://</code> path, with no server, no network and no
access to the other files. The standalone diagram files are one click away.</p>
<p><a href="graphify/use-cases.md">The five structural investigations</a> ·
<a href="../journal/07-architecture.md">Round 07 journal</a> ·
<a href="../README.md">Run report</a></p>
</header>
{"".join(sections)}
<footer>Rendered with the existing Archify 3.2.0 installation, which ran every validate, finalize
and browser-check gate. Each diagram is embedded as JSON and drawn from an iframe <code>srcdoc</code>,
so this page needs nothing from disk beyond itself. Archify has no use-case type: the three
use-case diagrams are architecture diagrams with actors kept outside the system boundary. The
board is a local public demo, with no authentication and no per-visitor vote limit.</footer>
</main>
<div id="viewer" aria-hidden="false">
<div class="bar"><strong></strong><button class="prev" aria-label="Previous diagram">‹ Prev</button><button class="next" aria-label="Next diagram">Next ›</button><button class="close">Close (Esc)</button></div>
<iframe title="Full-size diagram"></iframe>
</div>
{"".join(parts)}
<script>{SCRIPT}</script>
</body>
</html>
"""
    out = HERE / "index.html"
    out.write_text(page, encoding="utf-8")
    print(f"{out.name}: {out.stat().st_size:,} bytes, 14 diagrams inlined ({total:,} bytes of JSON)")


if __name__ == "__main__":
    main()
