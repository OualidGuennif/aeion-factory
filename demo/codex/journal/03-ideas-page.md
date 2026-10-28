# Round 03 — SSR page and enhanced form

Plan: share form normalization and domain validation, inject the existing store into Fresh state, render list and accessible form server-side, enhance submission in NewIdeaForm island. Preserve plain HTML POST/redirect/get. Small responsive token stylesheet with light/dark themes. No votes, filters, accounts or client routing.

Implemented and verified 40 tests, build, SSR/no-JS HTTP POST and browser enhancement. The browser showed too_short inline while retaining the draft, then created Offline mode through the island and reloaded the list. Inspected 1440px and 375px in both light and dark; no horizontal clipping was visible. Visual shipping approval remains user-owned; no deployment is requested.

A real precompile/defaultValue issue was fixed using controlled Preact fields. The regression now requires an actual value attribute, not a suffix match on defaultvalue. The escaping test originally demanded &gt; for every >; it was corrected to Preact's valid &lt;script> encoding while still asserting no executable script markup.

Evidence: evidence/03-red.txt, 03-quality-green.txt, 03-build-green.txt, 03-smoke.txt, 03-factory.txt; browser tool snapshots and four viewport/theme screenshots in the session.

Result:          done
Tests:           40 passed, 0 failed; build, HTTP and browser form checks PASS
Factory checks:  knowledge-check, doc-links, repo-health: PASS
Guard refusals:  0
Human help:      0 direct actions
Feedback:        none new
Elapsed:         8 minutes approximate
