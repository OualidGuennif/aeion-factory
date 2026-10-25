# Æion Factory

**A GitHub template for working with coding agents: clear instructions, linked documentation
and automatic checks.**

Use it to start a project or improve an existing repository. Factory gives you a repeatable
workflow: **plan → change → test → review**. Keep only the parts you need.

- **Instructions:** tell the agent how your project works in [AGENTS.md](AGENTS.md).
- **Context:** keep decisions and component docs in `knowledge/`, linked to the files they describe.
- **Checks:** catch broken links, missing doc updates and repository-size limits with Git and Python.
- **Procedures:** reuse skills and hooks for common tasks instead of repeating instructions.

The method is language-independent. Your project's compiler, linter and tests validate its code.
Hooks and plugins target Claude Code; other agents can follow `AGENTS.md` and the workflow.
Managed Claude runs enable a 250k compaction/checkpoint profile. Graphify/Archify analysis is
mandatory at adoption and after main updates; its isolated setup also requires Node and Chrome.
The observed 300k stop is not a qualified strict pre-request ceiling.

## Try it

Requires **Git and Python 3**. These checks run locally without a model account.

```bash
git clone https://github.com/OualidGuennif/aeion-factory.git
cd aeion-factory
tools/knowledge/knowledge-check
tools/knowledge/doc-links
tools/repo-health/repo-health
```

All three commands should exit successfully; the knowledge and link checks print `PASS`.
Shell integrations target macOS, Linux and WSL.

## Use it in your project

**New project:** [use this template](https://github.com/OualidGuennif/aeion-factory/generate),
then put your project description and build/test commands in `AGENTS.md`.

**Existing repository:** follow the [adoption guide](efficiency/00-EFFICIENCY.md), one phase at
a time. Your existing instructions and tools take precedence. Scheduled loops and external
services stay off until you choose to configure them.

**AI agents:** read [AGENTS.md](AGENTS.md) first. It points to the policies, commands and task state.

## Documentation

| Read | For |
| --- | --- |
| [Getting started](efficiency/00-EFFICIENCY.md) | Adopt the method step by step |
| [Agent workflow](Workflow_Agent.md) | Follow a task from plan to review |
| [Commands](command.md) | Run checks, skills and optional loops |
| [Build and test](knowledge/operations/build-and-test.md) | Verification commands and hook requirements |
| [Context safety](knowledge/operations/context-safety.md) | Handover, native compaction and the runtime guarantee boundary |
| [Architecture maintenance](knowledge/operations/architecture-maintenance.md) | Mandatory Graphify/Archify baseline and main refresh |

Factory works on its own. The optional [Æion modules](https://github.com/OualidGuennif/aeion-spaceship/blob/main/docs/modules.md)
cover security, audit, observability and integration when you need them.

License: [MIT](LICENSE). Credits: [CREDITS.md](CREDITS.md). Security: [SECURITY.md](SECURITY.md).
