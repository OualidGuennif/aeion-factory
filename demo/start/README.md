# Starting a harness

These notes are for the person who launches a run. Each folder holds the first message to paste into
one harness:

| Harness | First message | Open it in |
| --- | --- | --- |
| Claude Code | [`claude_code/START.md`](claude_code/START.md) | `demo/` |
| Codex | [`codex/START.md`](codex/START.md) | `demo/` |
| OpenCode | [`opencode/START.md`](opencode/START.md) | `demo/` |
| Pi | [`pi/START.md`](pi/START.md) | `demo/`, with the extension flag below |

Every message assumes the agent was opened in `demo/`, and every path in it starts there.

## Before any run
- **Tools on this machine:** Deno 2 (the app, and `ask callers`), Docker (round 06), Node and Chrome
  (Archify, round 07). Each run installs nothing on its own.
- **The graph:** `tools/architecture/ask` needs the Graphify venv in `.aeion/integrations/graphify-venv/`.
  It is already set up here. On another machine, run `tools/architecture/setup` once from the root.
- **A clean folder:** `demo/<harness>/` has an empty `journal/`, `feedback_for_aeion/` and `render/`,
  plus a `workspace/` copied from the factory with no app in it. To start again, archive the last run
  as [`../claude_code/archive/run-01/`](../claude_code/archive/run-01/SUMMARY.md) shows, then copy the
  factory again:
  ```bash
  rm -rf demo/<harness>/workspace && mkdir -p demo/<harness>/workspace && git archive HEAD -- . ':(exclude)demo' | tar -x -C demo/<harness>/workspace
  ```

## Skills and hooks, per harness
The skills live once, in `.claude/skills/`. `.agents/skills/` holds links to them for the other harnesses.
The hooks all call the same guards in `.claude/hooks/` and `tools/agents/hook.py`. The full runbook is
[`knowledge/operations/agent-compatibility.md`](../../knowledge/operations/agent-compatibility.md).

### Claude Code
- **Nothing to set up.** The root `CLAUDE.md`, the `.claude/settings.json` hooks and `.claude/skills/`
  are found from `demo/`.
- **Duplicate skills.** The skill list also shows the copy's own skills, as `demo/<harness>/workspace:<skill>`.
  Those belong to the copy; the agent uses the root ones.
- **Hooks check.** Type `/hooks` and look for the `PreToolUse` guards.

### Codex
- **Trust and hooks.** Trust the project in Codex's settings, enable the project hooks in `/hooks`, then
  restart Codex. A trusted project and trusted hooks are two separate approvals; both are needed.
- **Skills.** Codex finds them through the `.agents/skills/` links. Nothing to copy.
- **Commits.** Codex's sandbox writes only below `demo/`, so each `git commit` asks for your approval.

### OpenCode (2.1.4+)
- **Skills and hooks load on their own.** The root `opencode.json` points at the skills, and the plugin
  in `.opencode/plugins/factory/` runs the hooks.
- **Provider.** Connect it in OpenCode's own settings.
- **Database conflict.** If OpenCode refuses to start, use `tools/agents/run opencode --isolated` from the
  root. It uses a separate local profile, so you connect the provider once more there.

### Pi (1.4.0+)
- **Start command.** Pi loads project extensions only from the folder it starts in, so from `demo/` pass
  the hooks explicitly:
  ```bash
  cd demo && pi -e ../.pi/extensions/factory/index.js
  ```
- **Trust prompt.** Accept it, so Pi reads the project.
- **Skills.** Found through `.agents/skills/` in a parent folder.
- **Provider.** Connect it in Pi's own settings.
- **Live qualification.** Pi has never run live with the factory. This run is also that qualification,
  and any refusal or silence from the hooks is a feedback.
- **No sign-off at stop.** Pi has no hook for it, so the skill `sign-off` does that step.

## Check the hooks before round 00
In any harness, ask the agent to run `cat .env`. The guard must refuse it and name its rule. If the
command runs, or the agent reports no refusal, the hooks are not loaded. Fix the setup above before
going on.
