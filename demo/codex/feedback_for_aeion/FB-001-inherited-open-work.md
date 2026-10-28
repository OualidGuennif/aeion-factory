# FB-001 — A new demo copy inherits unrelated open tasks

Severity: low
Status: observed; base factory unchanged

Evidence: before app code, workspace/work/current.md contained the completed Claude run and unrelated native-hook/context tasks. The workspace is copied with git archive, including active project state. This is the already known FB-003 class, reproduced in Codex.

Impact: the harness can mistake old tasks for work it must perform.

Proposed fix: make the demo copy preparation replace work/current.md with an empty task template; keep the factory history in its own repository. In this run only the Codex copy's task state was replaced.
