---
type: Component
title: "Idea Board page"
description: "The home page: a server-rendered list of ideas and a form that works without JavaScript and is enhanced by an island."
status: draft
generated:
  by: aeion-factory/1.3
  at: 2026-10-28
sources:
  - id: home
    resource: ../../app/pages/home.tsx
    title: "Home handlers and page component"
  - id: route
    resource: ../../app/routes/index.tsx
    title: "The / route wiring"
  - id: form
    resource: ../../app/domain/form.ts
    title: "Form parsing and messages"
  - id: island
    resource: ../../app/islands/NewIdeaForm.tsx
    title: "The enhancing island"
  - id: fields
    resource: ../../app/components/IdeaFormFields.tsx
    title: "Form fields shared by the page and the island"
  - id: vote
    resource: ../../app/pages/vote.ts
    title: "The no-JavaScript vote handler"
  - id: vote-route
    resource: "../../app/routes/ideas/[id]/vote.ts"
    title: "The /ideas/:id/vote route wiring"
  - id: vote-island
    resource: ../../app/islands/VoteButton.tsx
    title: "The vote island"
  - id: shared
    resource: ../../app/store/shared.ts
    title: "The one lazily opened store the routes share"
  - id: styles
    resource: ../../app/assets/styles.css
    title: "Design tokens (light and dark) and layout"
  - id: policy
    resource: ../policies/ui-ux.md
    title: "UI and UX policy"
---

# Idea Board page

## Intent
Let a visitor read the board, and let a contributor add an idea from the browser, with or without
JavaScript, refusing exactly what the API refuses.

## Data sources
| Source | What is read | Owner | Freshness |
| --- | --- | --- | --- |
| Ideas store (`app/store/shared.ts`) | 20 ideas, newest or most voted first | this app | live, per request |

## Inputs
- `GET /?sort=recent|votes&tag=t&q=text`; any other `sort` reads as `recent`, and an invalid `tag` or `q` is dropped
  (the page is lenient; the API is strict, with the same `parseFilters`).
- `POST /ideas/:id/vote`, with an optional `sort` field to return to.
- `POST /` as `application/x-www-form-urlencoded` or `multipart/form-data`, with these fields:
  - `title`;
  - `description`;
  - `tags`: comma-separated; split, trimmed and lowercased, empties dropped, by `parseIdeaForm`.
- From the island: the same fields, sent as JSON to `POST /api/ideas`.

## Outputs
| Request | Status | Body |
| --- | --- | --- |
| `GET /` | 200 | `<h1>Idea Board</h1>`, the form, then the ideas (title, description, tags, votes, date) or "No ideas yet." |
| `POST /` valid | 303 | `Location: /` (post/redirect/get) |
| `POST /` invalid | 400 | the page again: values kept, the message next to the field, `aria-invalid` and `aria-describedby` set |
| `GET /?tag=ui&q=dark` | 200 | the filtered list, a line naming the active filters, a "Clear filters" link; "No ideas match these filters." when empty |
| `POST /ideas/:id/vote` | 303 | `Location: /` or `/?sort=votes` |
| `POST /ideas/:id/vote`, unknown id | 404 | plain text, nothing written |
| `POST /` from another site | 403 | Fresh `csrf()` (an `Origin` or `Sec-Fetch-Site` that is not this site) |

**Messages.** One per reason code, in `messages` (`app/domain/form.ts`). For example, `too_short` reads "Use at least 3 characters."

## Invariants
1. The page and the API refuse the same inputs with the same reason codes: both call `validateNewIdea`. Test: `app/pages/home_test.tsx` "POST / refuses what the API refuses".
2. User text is escaped. Test: `app/pages/home_test.tsx` "a script title is shown as text".
3. Without JavaScript the form still works: it is a plain `method="post"` form rendered on the server. Test: `app/pages/home_test.tsx` "the form posts to / without JavaScript".
4. Every control has a label, and an error is linked by `aria-describedby`. Test: `app/pages/home_test.tsx` "an error is linked to its field".
5. Colours, spacing and radii are tokens in `app/assets/styles.css`, with a light and a dark set. There are no inline styles. Test: `app/pages/home_test.tsx` "no inline styles".
6. `parseIdeaForm` is pure. Test: `app/domain/form_test.ts`.
7. Voting works without JavaScript: each idea has a `method="post"` form to `/ideas/:id/vote`; the `VoteButton` island
   posts to the API instead and updates the count in place. Test: `app/pages/vote_test.ts`.
8. The sort links mark the current one with `aria-current="page"`. Test: `app/pages/home_test.tsx` "sort by votes".
9. Tags are links to `/?tag=<tag>`; sort links, tag links and the search form keep the other filters. Test:
   `app/pages/home_test.tsx` "filters combine and are kept".
10. Filter values shown on the page are escaped. Test: `app/pages/home_test.tsx` "a script search is shown as text".
11. Every link to `/` sets `aria-current` itself: Fresh would otherwise mark it current or ancestor. Test:
    `app/pages/home_test.tsx` "filters combine and are kept" (exactly one `page` or `true`).

## Determinism
deterministic: plain code, no model in the loop.

## Acceptance checks
```bash
cd app && deno task test
curl -s localhost:8000/ | grep -c '<h1>Idea Board</h1>'                                   # 1
curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8000/ -d 'title=Offline%20mode'  # 303
curl -s -X POST localhost:8000/ -d 'title=x' | grep -c 'at least 3'                       # 1
```
Visual check, with screenshots in the journal: 375 px and 1440 px, light and dark.

## Out of scope
- An explicit theme switch: the system preference decides.
- Client-side routing.
