# Æion Factory

**A GitHub template for Claude Code, Codex and OpenCode: clear instructions, linked documentation,
shared skills and verifiable checks.**

Factory gives coding agents a repeatable workflow: **plan → change → test → review → merge**.
Your existing project instructions and the owner's decisions take precedence.

| Shared foundation | Where it lives |
| --- | --- |
| Project instructions and authority | [AGENTS.md](AGENTS.md) |
| Canonical policies, specs and decisions | [knowledge/](knowledge/index.md) |
| Open task state | `work/current.md` |
| Maintained skills | `.claude/skills/`; Codex discovers links in `.agents/skills/` |
| Tests and documentation checks | `tools/`, Git pre-commit and CI |
| Source-backed graph and architecture | Mandatory Graphify/Archify baseline and main refresh |

## 1. Prepare the repository

For a new project, [use this template](https://github.com/OualidGuennif/aeion-factory/generate).
For an existing project, follow [the adoption guide](efficiency/00-EFFICIENCY.md); merge with what
is already there. Adapt AGENTS.md, the architecture spec and analysis scope/views to your project.

For Factory itself:

```bash
git clone https://github.com/OualidGuennif/aeion-factory.git
cd aeion-factory
git config core.hooksPath tools/git-hooks
tools/knowledge/knowledge-check
tools/knowledge/doc-links
tools/repo-health/repo-health
```

Core checkers need Git and Python. The complete supported setup requires **Python 3.12+**
(excluding 3.14.1 for the current dependency pins), **Node 18+** and **Chrome/Chromium**.
Use macOS, Linux or WSL. Install your chosen agent separately using its official instructions:
[Claude Code](https://code.claude.com/docs/en/setup), [Codex](https://learn.chatgpt.com/docs/cli),
[OpenCode](https://opencode.ai/docs/). Keep accounts, API keys, providers and models in native user
configuration; never commit them to Factory.

## 2. Build the mandatory architecture baseline

```bash
python3 tools/architecture/setup
tools/architecture/refresh --target HEAD
```

This installs pinned tools locally, extracts the committed source/docs graph and validates three
source-backed architecture views, including browser checks. Results stay in ignored
`.factory/analysis/<sha>/`. After a new commit, build its baseline again. Every PR and main update
also runs analysis in CI. [Details and recovery](knowledge/operations/architecture-maintenance.md).

## 3. Start your agent

| Agent | Launch after the baseline | Native setup |
| --- | --- | --- |
| Claude Code | `tools/agents/run claude` | Trust the workspace; existing `.claude/settings.json`, skills and hooks load natively. |
| Codex | `tools/agents/run codex` | Trust the project, review and enable project hooks in `/hooks`, then restart the session. |
| OpenCode | `tools/agents/run opencode` | Root `opencode.json` and `.opencode/plugins/factory.js` load natively; connect your provider in OpenCode. |

All launchers enter the repository root and verify its exact-HEAD baseline. Native CLI arguments
can follow the agent name. The original `tools/context/run` remains the Claude-compatible entry.

For an OpenCode database-version conflict, `tools/agents/run opencode --isolated` uses a separate
project-local profile under `.factory/opencode/`. Connect the provider in that profile through
OpenCode; the existing user database is preserved. Do not copy stored credential files.

## What is enforced where?

| Capability | Claude Code | Codex local | OpenCode |
| --- | --- | --- | --- |
| AGENTS, Knowledge, shared skills, checker/PR workflow | Yes | Yes | Yes |
| Secret/Bash guards and edit feedback | Existing native hooks | Native hook adapter | Native plugin adapter |
| Verified handover/docs before compaction | Native hook | Native hook | Experimental compaction hook |
| Native compaction at 250k | Yes | Configured at 250k | Native model-window behavior; no fixed 250k claim |
| Observed 300k stop | Claude checkpoint profile | Unqualified | Unqualified |
| Absolute before-every-request 300k ceiling | Unqualified; strict mode refuses | Unqualified; strict mode refuses | Unqualified; strict mode refuses |

A transient Claude transcript delay blocks work and can recover when valid usage arrives. An
observed hard-limit stop stays latched. Codex's transcript format is not a stable token API;
the adapter does not pretend it is Claude's. OpenCode's idle sign-off is advisory. Hooks are
accidental-behavior safeguards alongside native sandbox/permission controls.

Project/hook trust is required. Hosted/cloud orchestration may ignore local hooks. Native
qualification, exact payload coverage and remaining limits are recorded in the
[compatibility runbook](knowledge/operations/agent-compatibility.md).

## 4. Work and deliver

1. Approve a small plan; update the owning spec; work on `task/<slug>`.
2. Implement, run relevant tests, update affected Knowledge and current task state.
3. Commit, refresh architecture for that SHA, open a PR and obtain the fresh review verdict.
4. Merge only with green required checks; wait for analysis on the exact merged main SHA.

[Agent workflow](Workflow_Agent.md) · [commands and skills](command.md) ·
[all validation commands](knowledge/operations/build-and-test.md).

Configure [main protection](knowledge/operations/github-protection.md) in each adopting GitHub
repository: template files do not copy GitHub settings. PRs and CI must be required, including
for admins; force-push and deletion stay disabled. Factory's seven AEion ecosystem main branches
were configured and re-read through the API on 2026-10-25.

Scheduled loops are **off by default**. Enabled local loops have a default 30-turn limit and
900-second deadline; read-only jobs permit fixed checker commands, and findings become issues.
[Loop setup](knowledge/operations/loops.md). Deployments follow the adopting project's procedure.

Factory works independently. Optional [Æion modules](https://github.com/OualidGuennif/aeion-spaceship/blob/main/docs/modules.md)
cover security, audit, observability and integration.

License: [MIT](LICENSE) · [Credits](CREDITS.md) · [Security](SECURITY.md).
