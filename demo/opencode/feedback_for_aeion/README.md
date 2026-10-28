# Feedback for Æion Factory — OpenCode run

One file per friction, numbered from 001 for this run, with evidence and a proposed fix. The run
does not fix the base factory itself.

| # | Title | Severity | Status |
| --- | --- | --- | --- |
| 001 | `ask` incremental rebuild missed a frontmatter-only spec edit | low | open |
| 002 | `cat` refused in any command containing a `cd`, even with an absolute path | low | open |
| 003 | concurrent demo runs share one working tree; the checkpoint fingerprint covers all of it | medium | open |

What was *not* filed, because it was correct behaviour or third-party friction (kept in the
journals instead): the secret-read refusal (`cat app/.env`, correct), the heredoc refusal (correct —
the write tool is the right answer), Fresh 2's handler shapes, `Deno.openKv`'s unstable flag and
missing folder creation, same-millisecond ULID ordering, and Deno lint's empty-interface rule.
