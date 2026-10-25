---
name: security-scan
description: Verifies security evidence for a sensitive change or periodic audit using available native tooling, project CI and independent review; uses claude-security inside Claude Code.
---

# Security scan

## Overview
Codex/OpenCode use the section below instead of the Claude plugin steps.

The `claude-security` plugin maps the code, searches each component, and has separate verifiers try to disprove every finding; only survivors are reported. Policy: `knowledge/policies/security.md`.

## Process
1. In Claude Code, installed? `/plugin install claude-security@claude-plugins-official` (project scope), `/reload-plugins`.
2. In Claude Code, changes: `/claude-security scan my branch at medium`. Codebase (weekly): `/claude-security` → scan codebase at medium, every top-level folder scanned or excluded on purpose.
3. Read `CLAUDE-SECURITY-*/CLAUDE-SECURITY-RESULTS.md` (the folder is git-ignored).
4. A finding in this PR's diff: fix it on the branch. Elsewhere: skill `loop-triage` opens an issue (severity, file:line, scenario, fix; no exploit detail beyond the fix).
5. Never paste a secret; never suppress a real finding.

## Red flags
Running it on every diff (it costs tokens); treating a skipped scan as a pass.

## Verification
- [ ] The scan's summary is quoted in the PR or the issue.

## Codex and OpenCode

Claude plugin slash commands do not run in these harnesses. Run the repository security commands
and inspect secret/dependency/SAST CI on the exact commit, then perform an independent sensitive
change review. Record the actual tools, scope and results. If the native plugin scan was not run,
say so; do not equate a different scan with claude-security or fabricate its report.
