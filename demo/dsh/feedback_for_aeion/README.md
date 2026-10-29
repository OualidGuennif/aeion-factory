# Feedback for Æion Factory — dsh run

One file per friction, numbered from 001 for this run. Each has severity, evidence with the real
output, a proposed fix and its status. Statuses: `open`, or `applied <sha>` once the base factory
carries the fix (the base is fixed there, never from this copy).

| FB | Title | Severity | Status |
| --- | --- | --- | --- |
| [001](FB-001-dsh-drops-session-start-context.md) | dsh drops the SessionStart context, so the checkpoint rule never reaches the model | medium | open |
| [002](FB-002-dsh-no-stop-sign-off.md) | dsh never sends Stop, so the sign-off hook never runs | medium | open |
| [003](FB-003-headless-commit-sandbox.md) | headless dsh cannot commit from `demo/`, and the brief says the sandbox asks | medium | open |
