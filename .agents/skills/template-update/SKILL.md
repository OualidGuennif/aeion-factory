---
name: template-update
description: Updates a project that adopted Æion Factory to a newer release, writing only the harness connector files and leaving the project's own instructions, settings, knowledge and changelog untouched, then naming every file a human must merge. Use when an adopted project should follow a new factory release, or when its connectors drifted from a release.
---

# Update an adopted project to a new release

The project's own text wins. A connector file belongs to the factory; everything the project wrote
belongs to the project. The whole skill is keeping those two apart.

## File classes

| Class | Files | Rule |
| --- | --- | --- |
| Contract | the connector list in `tools/agents/connectors.py` (`CONTRACT`): adapters, hooks, plugins, native registrations | **The factory wins, byte for byte.** Never hand-merge one: a difference is the bug. |
| Merge | `AGENTS.md`, `.claude/settings.json`, `.codex/config.toml`, `.devin/config.json` | **The project wins.** The factory's change arrives as a proposal you apply by hand. |
| User-owned | `VERSION`, `knowledge/`, `work/`, `CHANGELOG.md`, the project's build commands, its own specs | **Never written.** `VERSION` names the application's release, not the factory release it adopted. Ask before adding to the rest. |

## Steps

1. Read the target release's section of `CHANGELOG.md` and the parts of the diff that touch the
   merge files; say in one sentence what the update changes for this project.
2. Establish the factory reference the project adopted. Do **not** read it from the application's
   `VERSION`: that file is the application's own SemVer. Use the release tag or commit the project
   was adopted at, recorded by its owner or in its history; ask if it is not known.
3. From a factory checkout, run
   `tools/agents/template-update --from-ref <adopted-ref> --ref <tag> --root <project> --check` and
   read the three groups: contract files that differ, merge files the factory changed, and the
   untouched list.
4. Stop and ask. Show the merge list and what you propose for each file; the project's text stays
   unless its owner agrees to the factory's change.
5. Run it without `--check` to write the contract files and restore a launcher's executable bit.
   It leaves `VERSION`, `knowledge/`, `work/` and `CHANGELOG.md` byte-identical.
6. Merge each named file yourself, keeping the project's wording, build commands and rules; add the
   factory's new lines where they do not conflict, and say what you kept and why.
7. Verify: `tools/agents/adapter-check --root <project> --ref <tag>` is PASS (bytes, wiring, no
   linked connector, executable launchers), the project's own `tools/knowledge/doc-links` and
   build/tests pass, and the application's `VERSION` is unchanged.
8. Commit with the release named; do not tag, push or open the project's pull request unless asked.

## What this must never do

- Rewrite `AGENTS.md`, `knowledge/`, `work/`, `CHANGELOG.md`, `VERSION` or a merged settings file.
- Improve, tidy or modernise the project's own instructions during an update.
- Guess the factory baseline from `VERSION`; an application `0.1.0` is not factory `0.1.0`.
- Write through a symlinked connector or its parent. The update refuses the whole destination set
  before writing anything.
- Leave a contract file half-matched; a copy that differs from the reference is the failure the
  update exists to remove.
- Update a directory that carries no connector from the contract list.

## When the factory and the project disagree

The project's approach wins on anything it authored: its task shape, its build commands, its
policies, its domain specs. The factory wins on the files a harness loads, because a hand edit
there fails silently in the harness rather than in review. If a factory change makes the project's
own content wrong, propose the correction separately, with the evidence, instead of folding it into
the update.

## Branch references

`main` and `develop` are valid values for either `--from-ref` or `--ref` when someone downloaded a
branch instead of a release. A branch moves, so `--check` reports the drift as soon as it does; say
which references you used, and prefer tags for anything the project will keep.
