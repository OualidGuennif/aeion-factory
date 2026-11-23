---
id: 007
sequence: 7
title: "Content sanitization for user text"
area: foundation
size: M
parallel: false
phase: P0
tier: 3
write_paths: ["demo/forum-app/", "knowledge/components/agora-product.md", "knowledge/components/factory-architecture.md"]
depends_on: [006]
owner: builder
status: proposed
architecture: quarkus-postgresql-react-web-v1
architecture_digest: 33e7246cc390bdacfbf8da5d7a0b2d7ff48b0774f1833155ac725cb519f06c2e
---

# 007 — Content sanitization for user text

## Intent

Turn any submitted thread body into normalized plain Markdown and a small, attribute-free safe HTML subset with strict codepoint and byte caps, so a post never carries script, remote embeds or an oversized payload.

## Data sources

Frozen feature brief and merged dependency interfaces from [PLAN.md](../PLAN.md).
The approved [product architecture](../ARCHITECTURE.md) is Quarkus/Java + PostgreSQL +
React DOM/TypeScript web. Paths refer to the separate product repository, not Observability.
Content and model output are untrusted. Canonical definition: `tools/specs_a.py`.

## Inputs

**Delivery steps:**

1. Implement `ContentSanitizer.sanitize` and `ContentTooLargeException` with NFC normalization, 4000-codepoint / 32768-byte caps, and the attribute-free Markdown subset.
2. Wire `ContentSanitizer` into `ThreadService.create` and `ThreadsResource` (`body_html` on create/read/list and HTTP 413 `{"error": "content_too_large"}`).
3. Test XSS payloads, normalization/Markdown fixtures, supplementary Unicode codepoints, and 413 refusals without outbox writes.

**Scope:**

- Add public `local.aeion.forum.ContentSanitizer` with static `sanitize(String raw)` returning a public record (`markdown()`, `html()`) and nested public static `ContentTooLargeException extends RuntimeException` (message `"content_too_large"`). Null input normalizes to empty text (preserving the existing `400 {"error": "invalid_body"}` refusal on blank bodies).
- Normalize to Unicode NFC, convert CRLF/CR to LF, strip control/format/zero-width codepoints except LF and TAB, collapse horizontal whitespace outside fenced code blocks, strip non-code line edges, collapse blank-line runs to one blank line, and trim leading/trailing blank lines while preserving fenced code indentation and trailing spaces (idempotent normalization). Both raw and normalized text are capped at `4000` Unicode codepoints (supplementary characters such as `"😀".repeat(4000)` count as 4000 codepoints, not UTF-16 units) and rendered HTML is capped at `32768` UTF-8 bytes; exceeding either throws `ContentTooLargeException` without truncation.
- Render only attribute-free `p`, `strong`, `em`, `ul`, `ol`, `li`, `blockquote`, `pre`, and `code` elements (paragraphs `<p>...</p>` joining lines with one space, block outputs separated by one `\n` without trailing `\n`, `**bold**` -> `<strong>`, `*em*` -> `<em>`, `- item` -> `<ul><li>`, `1. item` -> `<ol><li>`, `> quote` -> `<blockquote><p>...</p></blockquote>`, and triple-backtick fences with optional ignored language label -> `<pre><code>...\n</code></pre>` with literal unparsed Markdown inside). Escape all HTML metacharacters (`<`, `>`, `&`, quotes) before emitting text so raw HTML, `<script>`, event handlers, links/images, and `javascript:`/`data:` URLs remain inert escaped text.
- In `ThreadService.create`, normalize before validating/storing `body` (persisting normalized plain Markdown in `threads.body`, never raw transport bytes) and map `ContentTooLargeException` to HTTP `413 {"error": "content_too_large"}` on `POST /api/threads` before any thread or outbox insert. In `ThreadsResource`, expose `"body"` (normalized plain Markdown) and `"body_html"` (derived safe HTML via `ContentSanitizer`) on `POST /api/threads`, `GET /api/threads`, and `GET /api/threads/{id}` (no DB schema migration required).

## Outputs

An artifact restricted to the declared write scopes, with checks and refusals described below.
The protected factory independently validates it; builder reports cannot certify completion.
Backend tests use JUnit/Quarkus and disposable PostgreSQL; browser behavior uses the React
production build. A previous SQLite/Expo receipt does not qualify this architecture.

## Invariants

Retain normalized plain Markdown in storage and derive sanitizer-produced HTML on output, never original transport bytes. Escape HTML metacharacters in the renderer and forbid all HTML attributes and executable URLs.

This invariant and the acceptance cases belong to planned protected check `agora-007`.
The supervisor freezes external acceptance before implementation; candidate code cannot change the verifier.

## Determinism

Use explicit bounds, versioned inputs, a frozen clock and seed where relevant. Model-generated
artifacts remain untrusted until checked; no model output grants runtime authority.

## Acceptance checks

- [ ] Authenticated `POST /api/threads` (with session cookie and `X-CSRF-Token`), `GET /api/threads/{id}`, and `GET /api/threads` return `"body"` as normalized plain Markdown and `"body_html"` using only attribute-free `p/strong/em/ul/ol/li/blockquote/pre/code` tags, rendering `<script>`, event handlers (`onerror`, `onload`, `onclick`), and `javascript:`/`data:` URLs as inert escaped text.
- [ ] A thread `body` exceeding `4000` Unicode codepoints (raw or normalized, within the `16 KiB` transport cap) is refused on `POST /api/threads` with HTTP `413 {"error": "content_too_large"}` and writes no thread or outbox row; `ContentSanitizer.sanitize` accepts `4000` supplementary codepoints (`"😀".repeat(4000)`) and enforces the `4000`-codepoint and `32768`-UTF-8-byte HTML caps in JUnit without truncation.
- [ ] Normalization and rendering are idempotent and byte-stable across create, read, and list for NFC, zero-width/control stripping, `**strong**`/`*em*`, lists, blockquotes, and fenced code blocks (` ```java\n  <x>  \n``` ` -> `<pre><code>  &lt;x&gt;  \n</code></pre>`).

**Test scenario:** Exercise 30 XSS payloads, Markdown subset and NFC/control/zero-width normalization fixtures, idempotent re-submission (`body` and `body_html` unchanged), and `> 4000`-codepoint `413 {"error": "content_too_large"}` refusal over HTTP (`POST /api/threads` / `GET /api/threads/{id}` / `GET /api/threads`), plus supplementary-Unicode codepoint and `32768`-byte HTML bounds in JUnit.

## Out of scope

- Images, tables, links/autolinks, iframes, HTML attributes or any remote resource.
- Client-side sanitization as the primary control or a new database column/migration.
