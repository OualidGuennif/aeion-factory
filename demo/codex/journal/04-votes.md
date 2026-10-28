# Round 04 — Atomic votes and sorting

Plan: add vote index on creation, optimistic vote transaction with <=10 retries, votes/recent query validation and ordering, HTML vote endpoint preserving sort, VoteButton enhancement. Test 25 concurrent writes plus exactly one index key and forced exhaustion. No accounts, deduplication or un-voting.

Added compare-and-set votes with the vote index moved atomically, bounded jittered retries and explicit busy exhaustion. 25 simultaneous store votes all succeeded; final votes=25 and exactly one index key. Forced conflict test proves 10 attempts and no mutation; API proves 503 busy. HTTP smoke performed three concurrent votes and verified final count=3 plus vote sorting.

Evidence: evidence/04-red.txt, 04-quality.txt, 04-build.txt, 04-smoke.txt, 04-factory.txt. HTML route and island browser checks will be repeated on the completed filter page.

Result:          done
Tests:           48 passed, 0 failed; build and HTTP smoke PASS
Factory checks:  knowledge-check, doc-links, repo-health: PASS
Guard refusals:  0
Human help:      0 direct actions
Feedback:        none new
Elapsed:         4 minutes approximate
