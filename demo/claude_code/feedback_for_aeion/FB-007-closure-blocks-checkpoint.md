# FB-007: at the 250k alert, closure can deadlock on the checkpoint command

- **Severity:** medium (the session cannot compact without the owner's terminal)
- **Found in:** round 03
- **Status:** open

## Evidence
At the 250k alert, `tools/context/budget.py` lets only a closed set of tools through. For Bash it
admits only these 8 words: `python3 tools/context/budget.py checkpoint --session <id> --base <ref> --verify`.

1. The Bash working directory had stayed in `demo/claude_code/workspace` after a round's tests. The
   relative command then ran the **copy's** `budget.py`. That one looked for
   `workspace/.aeion/context/<session>.json` and refused with `No such file`.
2. Every way back to the repository root was refused: a `cd <root> && …` prefix, an absolute path to
   `budget.py`, and a bare `cd`. ToolSearch was blocked too, so no other tool could be loaded.
   Writing to `demo/` was refused as well, which is why this file was written only after compaction.
3. `/compact` is held by PreCompact until a verified checkpoint exists. The owner had to run the
   checkpoint from the repository root in their own terminal.
4. That first run printed only `Checkpoint refused: complete all handover sections first`. The real
   cause was one heading, `## Completed (commits on develop)`, because the check expects exactly
   `## Completed`. The message did not name it.

After the fix to the heading, the owner's run printed `Checkpoint: PASS`, and compaction went through.

## Proposed fix
- At the alert, admit the checkpoint in any form that resolves to **this root's** `budget.py`: an
  absolute path, a `cd <root> &&` prefix, or a run from any working directory. Also admit a bare
  `cd <root>`.
- Name the missing or malformed headings in the refusal, for example
  `missing heading: ## Completed`.
- Tests in `tools/context/tests/test_budget.py`: each admitted form passes, `cd /elsewhere && …`
  stays refused, and the refusal names the heading.
