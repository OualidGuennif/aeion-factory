# OpenCode integration

Read the [setup runbook](../knowledge/operations/agent-compatibility.md).
Root opencode.json enables native auto-compaction and points at the maintained Claude skill
source. The local plugin reuses existing Python guards, edit checks and handover checkpoints.
OpenCode also discovers the shared .agents/skills links; bodies are maintained once.

After the mandatory baseline, launch with `tools/agents/run opencode`. The plugin package is
pinned for the qualified runtime; let the native tool install its project dependencies.

If your existing OpenCode database is incompatible, `tools/agents/run opencode --isolated`
selects project-local XDG data/config/state/cache under ignored .factory/opencode. Connect your
provider through OpenCode's own UI for that separate profile; never copy stored credential files.
The existing user database and configuration remain yours.

The compaction callback is experimental upstream. It refuses compaction without the verified
handover and injects its recovery pointer. Idle sign-off is advisory feedback, not a forced
continuation. OpenCode controls the model's native compaction window; no invented fixed 250k
setting or strict/observed 300k runtime cap is advertised.
