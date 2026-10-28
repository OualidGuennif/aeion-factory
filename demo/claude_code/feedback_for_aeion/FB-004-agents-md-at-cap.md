# FB-004: `AGENTS.md` ships at its 120-line cap but asks you to add lines

- **Severity:** medium (the first adoption step fails two checks)
- **Found in:** round 01
- **Status:** open

## Evidence
`AGENTS.md` is exactly 120 lines, and `knowledge-check` and `repo-health` fail above 120. It asks for two edits:
- "Replace this paragraph with what *your* project is";
- "Add your project's own build and test commands here, copied from CI".

When I followed both with 6 short lines, both checks failed:

```text
FAIL AGENTS.md: over 120 lines; route to docs instead of explaining     (knowledge-check)
FAIL AGENTS.md over 120 lines                                           (repo-health)
```

I fitted the app commands on one line and shortened my paragraph. The file can absorb a project's commands only by squeezing them, and a real project has more than two commands.

## Proposed fix
- Leave headroom in the template, about 10 lines. The seven lines of the factory's own test suite under "Build and test" can become one line: `tools/check-all`, or a pointer to the CI job that already lists them.
- Or have the cap count only the lines the project adds. That is harder to explain, so headroom is the better fix.
