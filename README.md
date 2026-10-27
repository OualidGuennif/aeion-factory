# Æion Factory

**A repository template for Claude Code, Codex, OpenCode, Devin and Factory's Droid: shared instructions, linked
specs, reusable skills and automatic checks.**

Æion Factory organizes the work around **plan → change → test → review → merge**. Your project's
existing instructions and the owner's decisions take precedence.

| Part | Purpose |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Project instructions, authority and workflow |
| [Knowledge](knowledge/index.md) | Canonical policies, component specs and decisions |
| `work/current.md` | Open tasks only |
| `.claude/skills/` | Maintained skill bodies; `.agents/skills/` exposes them to Codex, Devin and Droid |
| `.claude/`, `.codex/`, `.opencode/`, `.devin/`, `.factory/` | Native configuration/adapters for each agent (`.factory/` is Droid's) |
| `.aeion/` (ignored) | Æion Factory's local state: analysis, context checkpoints, loop bodies |
| `tools/` and GitHub CI | Documentation checks, tests and source-backed architecture |

## Requirements

Git and **Python 3.12+** for the checks and hooks. Shell tools support macOS, Linux and WSL.
The recommended architecture baseline also needs **Node 18+** and **Chrome/Chromium** (Python
3.14.1 excluded for its pins); it is installed only when you say yes. Install `gh` for the GitHub
PR workflow and your chosen agent separately:

- [Claude Code](https://code.claude.com/docs/en/setup)
- [Codex](https://learn.chatgpt.com/docs/cli)
- [OpenCode V2](https://opencode.ai/v2/docs/) — 2.1.4+ for Æion Factory's native plugin
- [Devin CLI](https://docs.devin.ai/cli/extensibility) — reads `.devin/`, `AGENTS.md` and `.agents/skills`
- [Droid](https://docs.factory.ai/cli/configuration/hooks-guide), the CLI of Factory (factory.ai), a separate
  product — reads `.factory/settings.json`, `AGENTS.md` and `.agents/skills`

Keep authentication, provider and model choices in the agent's native user settings. Never
commit credentials to the project.

## Quick start: try it, install nothing

```bash
git clone https://github.com/OualidGuennif/aeion-factory.git && cd aeion-factory
git config aeion.mode local    # optional, this clone's local config: play on main, no PR/CI ritual
tools/agents/run claude        # or: codex, opencode (2.1.4+), devin, droid
```

The launcher applies each agent's checked profile; the hooks and skills load from the repository,
and nothing is installed. The safety guards (secrets,
Git hook and force-push bypasses, large dumps) stay on in local mode. `git config --unset
aeion.mode` returns to the team flow. The agent recommends the architecture baseline and asks
before installing it: on a work computer, check your company's policy first.

## How to: new project

1. [Create a repository from this template](https://github.com/OualidGuennif/aeion-factory/generate),
   then clone your new repository and open its folder.
2. Start **one** of the agents below in that folder. These initial sessions prepare the project;
   use the managed launchers once setup and the baseline are complete.

   ```bash
   claude       # Claude Code
   codex        # Codex
   opencode     # OpenCode V2
   devin        # Devin CLI
   droid        # Droid (factory.ai)
   ```

3. Give the agent this setup request:

   > Read AGENTS.md, README.md and efficiency/00-EFFICIENCY.md. Prepare Æion Factory for this new
   > project: describe the project and owner, add its actual build/test commands, adapt the
   > architecture spec and analysis scope/views, and configure my chosen agent's native setup.
   > Run the checks. Ask me before enabling the Git pre-commit checks and before installing the
   > recommended Graphify/Archify baseline; tell me what it installs first. Keep one maintained
   > source for instructions, Knowledge and skills. Report anything that still needs
   > configuration. Wait for approval before implementing application features.

4. Complete the native workspace/project trust prompts. In Codex, also review and enable the
   project hooks in `/hooks`, then restart the session. For OpenCode, connect your provider
   through its native interface. For Devin and Droid, approve the project hooks if asked.
5. Confirm setup and start normal work through the managed launcher below. Configure
   [GitHub main protection](knowledge/operations/github-protection.md) in the new repository;
   GitHub settings are not copied by templates.

## How to: existing project

1. Open your **existing project folder** with Claude Code, Codex or OpenCode. Keep its current
   instructions, configuration, tests and Git history.
2. Make a local reference copy of Æion Factory, or point the agent at a reference folder you already
   have:

   ```bash
   git clone https://github.com/OualidGuennif/aeion-factory.git ../aeion-factory-reference
   ```

3. Give the agent this adoption request, replacing the reference path:

   > Read ../aeion-factory-reference/AGENTS.md, efficiency/00-EFFICIENCY.md and the adopt skill.
   > Inspect this project's existing instructions, docs, CI, skills and hooks first. Propose the
   > smallest adoption plan, one phase at a time. Merge useful Æion Factory pieces into what exists;
   > preserve my project's authority, conventions and working tools. Include native setup for my
   > agent, linked specs and relevant checks; offer the recommended architecture baseline and ask
   > me before installing anything. Wait for my approval before changing files.

4. Approve the fitting phases, validate each one and deliver through your project's PR workflow.
   Use [the adoption guide](efficiency/00-EFFICIENCY.md) and
   [runtime setup](knowledge/operations/agent-compatibility.md) for exact requirements.

## Start a prepared project

Run these from the repository root. Additional arguments are native CLI arguments.

| Agent | Command | Configuration |
| --- | --- | --- |
| Claude Code | `tools/agents/run claude` | Existing `.claude/settings.json`, hooks and skills |
| Codex | `tools/agents/run codex` | Trusted `.codex/config.toml` / `hooks.json`, shared `.agents/skills` |
| OpenCode | `tools/agents/run opencode` | Root `opencode.json`, native V2 plugin in `.opencode/plugins/factory/` |
| Devin CLI | `tools/agents/run devin` | `.devin/hooks.v1.json` and `config.json`, `AGENTS.md`, shared `.agents/skills` |
| Droid (factory.ai) | `tools/agents/run droid` | `.factory/settings.json` hooks, `AGENTS.md`, shared `.agents/skills` |

The launchers enter the project root and check the architecture baseline for the current commit;
without one they recommend it and continue. The original Claude entry point, `tools/context/run`,
also remains available.

## Available commands

| Command | What it does |
| --- | --- |
| `git config core.hooksPath tools/git-hooks` | Enable local pre-commit checks |
| `tools/knowledge/knowledge-check` | Validate Knowledge format, public links and task-state limits |
| `tools/knowledge/doc-links` | Validate documentation/code links |
| `tools/knowledge/doc-links --diff origin/main --worktree` | Check affected docs for committed and local changes |
| `tools/knowledge/doc-links --for path/to/file` | Find the docs covering a file |
| `tools/repo-health/repo-health --json` | Show repository size/comment/structure checks |
| `git config aeion.mode local` | Local play in this clone's local config: commit on main, no PR/CI ritual (`--unset` to undo) |
| `python3 tools/architecture/setup` | Install pinned Graphify/Archify into `.aeion/` (only on your yes) |
| `tools/architecture/refresh --target HEAD` | Build the recommended initial/updated source baseline |
| `tools/architecture/refresh --target HEAD --base origin/main` | Analyze the committed change and its comparison |
| `tools/architecture/refresh --check --target HEAD` | Verify the persisted baseline and artifact hashes |
| `tools/agents/run <claude\|codex\|opencode\|devin\|droid>` | Start a managed native agent |
| `python3 tools/context/budget.py checkpoint --session <id> --base origin/main --verify` | Verify handover, docs and source state before compaction |
| `loops/orchestrator.sh <job> --dry-run` | Inspect loop settings without launching an agent |
| `loops/orchestrator.sh inner --issue <n>` | Run one approved `agent-ready` issue when loops are enabled |
| `tools/efficiency/bundle` | Rebuild the portable seven-phase guide |

Loop jobs: `inner`, `middle`, `outer`, `docs`, `security`, `watch`, `retro`. They stay off until
configured. Enabled local jobs default to 30 turns and a 900-second deadline.
[Loop configuration](knowledge/operations/loops.md) · [all tests](knowledge/operations/build-and-test.md).

## Available skills

Ask the agent to use a named skill; Claude Code also supports `/name`, and Codex supports `$name`.
OpenCode loads skills through its native skill tool; Devin and Droid read `.agents/skills`. Any agent can
open `.agents/skills/<name>/SKILL.md` directly.

| Skills | Use them for |
| --- | --- |
| `adopt` | Introduce Æion Factory into an existing project |
| `plan`, `spec` | Inspect and approve a change, then define its contract |
| `build`, `test`, `debug` | Implement, verify and investigate failures |
| `okf-update`, `sign-off` | Maintain Knowledge and finish a task with evidence |
| `pr-review`, `ship` | Obtain fresh review and deliver behind green checks |
| `security-scan` | Use native/project security tooling and report its actual coverage |
| `loop-triage`, `tech-watch` | Triage findings and evaluate external changes |
| `pr-taste`, `retro` | Retain owner preferences and useful lessons |

## Context and architecture

Shared [intake guards](knowledge/policies/bounded-intake.md) refuse obvious large full reads and
dumps before execution. Use targeted ranges, limited searches and summaries; no output is rewritten.

Before compaction, complete the active handover, current task and affected docs, then verify the
checkpoint. Claude and Codex configure native compaction at 250k; OpenCode uses its native model
window. Only the Claude profile implements the observed 300k stop. An absolute pre-request 300k
ceiling remains unqualified; strict mode refuses rather than claiming it.

Graphify/Archify analyze committed source and documentation in CI after every main update, and
locally once you approve their install. Generated output stays outside tracked source. Keep the canonical architecture spec
current and wait for the exact merged commit's analysis before declaring delivery complete.

[Agent workflow](Workflow_Agent.md) · [command reference](command.md) ·
[agent compatibility](knowledge/operations/agent-compatibility.md) ·
[context safety](knowledge/operations/context-safety.md) ·
[architecture maintenance](knowledge/operations/architecture-maintenance.md).

Æion Factory works independently. Optional [Æion modules](https://github.com/OualidGuennif/aeion-spaceship/blob/main/docs/modules.md)
cover security, audit, observability and integration.

License: [MIT](LICENSE) · [Credits](CREDITS.md) · [Security](SECURITY.md).
