---
type: Policy
title: "The owner's preferences"
description: "Durable preferences the owner stated in chat or on pull requests, one line each with its source; the skill pr-taste adds to it. A more specific policy wins."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: skill
    resource: ../../.claude/skills/pr-taste/SKILL.md
    title: "How entries are captured"
---

# The owner's preferences

What the owner asked for that a reviewer should not have to ask again. One line each, newest last
under its heading: `- <preference> (<source>, YYYY-MM-DD)`.

## Workflow

- Never install Graphify/Archify (or anything outside the repository's existing tools) without the
  user's explicit yes; say the baseline is strongly recommended and ask whether the machine is a
  work computer first. This replaces the Factory's mandatory pre-run baseline (chat, 2026-10-27)
- Colleagues may play locally without a Git/CI cycle: local mode commits on `main` (chat, 2026-10-27)
- Devin is a supported agent alongside Claude Code, Codex and OpenCode (chat, 2026-10-27)

## Engineering

- (none yet)

## UI

- (none yet)

## Checkable, no hook yet

- (none yet)
