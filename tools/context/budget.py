#!/usr/bin/env python3
# Spec: knowledge/operations/context-safety.md
"""Native-usage checkpoints and atomic handover receipts; not pre-request admission control."""
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/hooks"))
from secret_names import is_secret  # noqa: E402
from project_files import git_active, project_files  # noqa: E402
WARNING = 250_000
LIMIT = 300_000
MAX_TAIL = 4 * 1024 * 1024
FIELDS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
DOC_ROOTS = ("knowledge/", "work/", "efficiency/")
DOC_FILES = {"AGENTS.md", "CLAUDE.md", "README.md", "command.md", "Workflow_Agent.md", "CREDITS.md"}
CHECKS = (("tools/knowledge/knowledge-check",), ("tools/repo-health/repo-health",))


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(content)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def session_id(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", value):
        raise ValueError("invalid session identifier")
    return value


def identity(event):
    parent = session_id(event.get("session_id"))
    agent = event.get("agent_id")
    if agent is None:
        return parent, event.get("transcript_path"), parent
    agent = session_id(session_id(agent).removeprefix("agent-"))
    key = "agent-" + hashlib.sha256(f"{parent}/{agent}".encode()).hexdigest()[:40]
    transcript = Path(event.get("agent_transcript_path") or event["transcript_path"])
    stem = "agent-" + agent.removeprefix("agent-")
    subagents = Path(event.get("transcript_path") or transcript).parent / parent / "subagents"
    if transcript.stem == parent:
        transcript = subagents / f"{stem}.jsonl"
    # A workflow's agents write under subagents/workflows/<run>/; without that path every call is denied.
    if not transcript.exists():
        transcript = next(iter(sorted(subagents.glob(f"workflows/*/{stem}.jsonl"))), transcript)
    if transcript.stem not in {agent, stem}:
        raise ValueError("subagent usage must not reuse its parent's transcript")
    return key, str(transcript), transcript.stem


@contextmanager
def locked(root, session):
    folder = root / ".aeion/context"
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / f"{session}.lock").open("a") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        yield folder / f"{session}.json"


def native_usage(path, session):
    transcript = Path(path)
    if transcript.is_symlink() or transcript.name != f"{session}.jsonl":
        raise ValueError("usage must come from this session's regular JSONL transcript")
    if not transcript.exists():
        return None
    with transcript.open("rb") as stream:
        size = stream.seek(0, 2)
        start = max(0, size - MAX_TAIL)
        stream.seek(start)
        if start:
            stream.readline()
        tail = stream.read(MAX_TAIL)
        lines = tail.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        try:
            record = json.loads(lines[index])
        except json.JSONDecodeError:
            if index == len(lines) - 1 and not tail.endswith(b"\n"):
                return None
            raise
        if not isinstance(record, dict):
            raise ValueError("invalid transcript record")
        if record.get("subtype") == "compact_boundary":
            return None
        if record.get("type") != "assistant":
            continue
        message = record.get("message", {})
        if not isinstance(message, dict):
            raise ValueError("invalid transcript record")
        # API errors and hook stops are written as synthetic assistant records with zero tokens: they
        # were never sent, so reading them as the latest request would block every later prompt.
        if message.get("model") == "<synthetic>":
            continue
        usage = message.get("usage")
        if usage is None:
            continue
        if not isinstance(usage, dict) or any(type(usage.get(key)) is not int or usage[key] < 0 for key in FIELDS):
            raise ValueError("invalid native token counts")
        return sum(usage[key] for key in FIELDS) or None
    return None


def observed_usage(path, session):
    # Native transcripts are asynchronous; wait briefly without granting unmeasured work.
    for attempt in range(3):
        usage = native_usage(path, session)
        if usage is not None:
            return usage
        if attempt < 2:
            time.sleep(0.05)
    return None


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


def checkpoint_command(root, session):
    """The closure command for this folder: work merges into develop when it exists, else main; no git, no base."""
    command = f"python3 tools/context/budget.py checkpoint --session {session}"
    try:
        if not git_active(root):
            return command + " --verify"
    except subprocess.SubprocessError:
        pass
    develop = subprocess.run(["git", "rev-parse", "--verify", "--quiet", "origin/develop"], cwd=root,
                             capture_output=True, check=False).returncode == 0
    return command + f" --base {'origin/develop' if develop else 'origin/main'} --verify"


def fingerprint(root):
    # Include untracked task files and tracked bytes, without following symlinks.
    # A plain folder has no HEAD: its files alone make the fingerprint.
    digest = hashlib.sha256(git(root, "rev-parse", "HEAD") if git_active(root) else b"no-git")
    for rel in project_files(root, untracked=True):
        raw = os.fsencode(rel)
        if rel.startswith(("work/handovers/", ".aeion/")):
            continue
        name = Path(rel).name
        if is_secret(name):
            continue
        path = root / rel
        digest.update(raw + b"\0")
        if path.is_symlink():
            digest.update(os.fsencode(os.readlink(path)))
        elif path.is_file():
            digest.update(hashlib.sha256(path.read_bytes()).digest())
        else:
            digest.update(b"deleted")
    return digest.hexdigest()


def handover_path(root, session):
    return root / "work/handovers" / f"{session}.md"


def ensure_handover(root, session):
    path = handover_path(root, session)
    if not path.exists():
        atomic(path, f"# Handover {session}\n\n## Scope\nTODO\n\n## Completed\nTODO\n\n"
               "## Remaining\nTODO\n\n## Constraints\nTODO\n\n## Evidence\nTODO\n")
    return path


def ready(root, session, state):
    handover = handover_path(root, session)
    receipt = state.get("checkpoint", {})
    return (handover.is_file() and receipt.get("tree") == fingerprint(root)
            and receipt.get("handover") == hashlib.sha256(handover.read_bytes()).hexdigest())


def closure_tool(root, event):
    tool = event.get("tool_name")
    data = event.get("tool_input", {})
    if not isinstance(data, dict):
        return False
    if tool in {"Read", "Grep", "Glob"}:
        return True
    if tool in {"Edit", "Write"}:
        path = Path(data.get("file_path", "")).resolve()
        if not path.is_relative_to(root):
            return False
        rel = path.relative_to(root).as_posix()
        return rel in DOC_FILES or rel.startswith(DOC_ROOTS)
    if tool == "Bash":
        command = data.get("command", "")
        if not isinstance(command, str):
            return False
        fixed = {"tools/knowledge/knowledge-check", "tools/knowledge/doc-links", "tools/repo-health/repo-health",
                 "git status --short", "git diff --stat", "git diff --check"}
        if command.strip() in fixed:
            return True
        try:
            words = shlex.split(command)
        except ValueError:
            return False
        return checkpoint_call(root, event, words)
    return False


def checkpoint_call(root, event, words):
    """This root's checkpoint from any working directory, since a shell left in a subfolder must still
    close: `[cd <root> &&] python3 <its budget.py> checkpoint --session <this session> [--base <ref>]
    --verify`, or a bare `cd <root>`. Paths are resolved, never trusted by spelling."""
    here = Path(event.get("cwd") or root)
    if words[:1] == ["cd"]:
        if len(words) < 2 or (here / words[1]).resolve() != root:
            return False
        if len(words) == 2:
            return True
        if words[2] != "&&":
            return False
        here, words = root, words[3:]
    if len(words) < 2 or words[0] != "python3" or (here / words[1]).resolve() != root / "tools/context/budget.py":
        return False
    rest = words[2:]
    if rest[:3] != ["checkpoint", "--session", event["session_id"]] or rest[-1:] != ["--verify"]:
        return False
    # A plain folder has no base; a repository names one ref.
    return len(rest) == 4 or (len(rest) == 6 and rest[3] == "--base"
                              and re.fullmatch(r"[A-Za-z0-9_./-]+", rest[4]) is not None)


def stop(event_name, reason):
    if event_name == "PreCompact":
        return {"decision": "block", "reason": reason}
    return {"continue": False, "stopReason": reason, "systemMessage": reason}


def handle(root, event):
    root = root.resolve()
    if not isinstance(event, dict):
        raise ValueError("hook input must be an object")
    session, transcript, transcript_id = identity(event)
    name = event.get("hook_event_name")
    if name not in {"SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "PreCompact", "Stop", "SubagentStop"}:
        raise ValueError("unsupported control event")
    with locked(root, session) as file:
        state = json.loads(file.read_text()) if file.exists() else {"epoch": 0, "state": "RUNNING"}
        state["owner_session"] = event["session_id"]
        state["agent_id"] = event.get("agent_id")
        # The skeleton is created only when closure needs it, so ordinary sessions and subagents leave none.
        handover = handover_path(root, session)
        compact_verified = name == "SessionStart" and event.get("source") == "compact" and ready(root, session, state)
        if name == "SessionStart" and event.get("source") == "compact" and state.get("state") != "STOPPED":
            state = {"epoch": state["epoch"] + 1, "state": "RECOVERING", "warning_pending": state.get("warning_pending", False)}
        result = {}
        if state.get("state") == "STOPPED":
            result = stop(name, "Æion Factory context run is stopped; start a new validated session from its handover.")
        elif name == "SessionStart":
            context = "Æion Factory checkpoint profile: 250k handover/compact, 300k observed stop; not a strict ceiling."
            if handover.is_file():
                context += f" Recovery: {handover.relative_to(root)}"
            result = {"hookSpecificOutput": {"hookEventName": name, "additionalContext": context}}
            if state.pop("warning_pending", False):
                message = ("Æion Factory 250k alert: a verified handover was retained before compaction." if compact_verified
                           else "Æion Factory 250k alert: closure remains required; verify the handover/docs before compaction.")
                result["systemMessage"] = message
                result["hookSpecificOutput"]["additionalContext"] += "\n" + message
        else:
            try:
                usage = observed_usage(transcript, transcript_id)
            except (ValueError, OSError, TypeError, AttributeError):
                state["state"] = "STOPPED"
                atomic(file, json.dumps(state, sort_keys=True) + "\n")
                return stop(name, "Æion Factory native usage is invalid; refusing further work.")
            state["observed_tokens"] = usage
            if usage is None and name == "UserPromptSubmit" and not state.get("bootstrapped"):
                state["bootstrapped"] = True
            elif usage is None:
                reason = "Æion Factory native usage temporarily unavailable; work is blocked. Retry after transcript persistence; no terminal stop was latched."
                # Transcripts persist asynchronously: deny only this call so the agent can retry it, not stop the agent.
                if name == "PreToolUse":
                    result = {"hookSpecificOutput": {"hookEventName": name, "permissionDecision": "deny", "permissionDecisionReason": reason}}
                elif name != "PostToolUse":
                    result = stop(name, reason)
            elif usage >= LIMIT:
                state["state"] = "STOPPED"
                ensure_handover(root, session)
                result = stop(name, "Æion Factory observed 300k context limit reached; task remains incomplete. Read the handover.")
            else:
                state["bootstrapped"] = True
                if usage >= WARNING and state["state"] != "HANDOVER_REQUIRED":
                    state["state"] = "HANDOVER_REQUIRED"
                    state["warning_pending"] = True
                if name == "PreCompact":
                    if not ready(root, session, state):
                        ensure_handover(root, session)
                        result = stop(name, f"Fill {handover.relative_to(root)}, then create a verified checkpoint before compaction: {checkpoint_command(root, session)}")
                elif state["state"] == "HANDOVER_REQUIRED":
                    ensure_handover(root, session)
                    first = state.pop("warning_pending", False)
                    message = f"Æion Factory 250k alert: finish closure only, update {handover.relative_to(root)}, work/current.md and affected docs; verify the checkpoint before compaction."
                    if name == "PreToolUse" and not closure_tool(root, {**event, "session_id": session}):
                        result = {"hookSpecificOutput": {"hookEventName": name, "permissionDecision": "deny", "permissionDecisionReason": message}}
                    elif name in {"Stop", "SubagentStop"}:
                        result = stop(name, message + " Task has not been signed off.")
                    elif first and name in {"PreToolUse", "PostToolUse", "UserPromptSubmit"}:
                        result = {"systemMessage": message, "hookSpecificOutput": {"hookEventName": name, "additionalContext": message}}
                    if first:
                        result["systemMessage"] = message
                elif state["state"] == "RECOVERING":
                    state["state"] = "RUNNING"
            state["source"] = "current-session native transcript usage"
        atomic(file, json.dumps(state, sort_keys=True) + "\n")
        return result


def checkpoint(root, session, base):
    # Without git there is no base to diff, no task state ritual and no commit to compare.
    repository = git_active(root)
    if repository and base is None:
        raise ValueError("--base is required in a git repository")
    if repository:
        base = git(root, "rev-parse", "--verify", "--end-of-options", f"{base}^{{commit}}").decode().strip()
    with locked(root, session) as file:
        state = json.loads(file.read_text())
        if state["state"] == "STOPPED":
            raise ValueError("a stopped run cannot request another closure pass")
        handover = ensure_handover(root, session)
        text = handover.read_text()
        # Name each fault: a heading spelled `## Completed (commits)` reads as complete to a person.
        missing = [f"## {key}" for key in ("Scope", "Completed", "Remaining", "Constraints", "Evidence") if f"## {key}\n" not in text]
        if missing or "TODO" in text:
            faults = ([f"missing heading{'s' if len(missing) > 1 else ''}: {', '.join(missing)} (exact line)"] if missing else []) \
                + (["a section still reads TODO"] if "TODO" in text else [])
            raise ValueError(f"complete all handover sections first: {'; '.join(faults)}")
        before = fingerprint(root)
        diff = (("tools/knowledge/doc-links", "--diff", base, "--worktree"),) if repository else ()
        for command in (*CHECKS, *diff):
            subprocess.run(command, cwd=root, check=True, timeout=30, stdout=subprocess.DEVNULL)
        changed = set() if not repository else set(git(root, "diff", "--name-only", "-z", base).decode().split("\0")) - {""}
        changed |= {os.fsdecode(path) for path in (git(root, "ls-files", "--others", "--exclude-standard", "-z") if repository else b"").split(b"\0")
                    if path and not os.fsdecode(path).startswith((".aeion/", "work/handovers/"))}
        # Local play (git config aeion.mode local) keeps no work/current.md entry.
        local = not repository or subprocess.run(["git", "config", "--local", "--get", "aeion.mode"], cwd=root, capture_output=True, text=True).stdout.strip() == "local"
        if changed and not local and "work/current.md" not in changed:
            raise ValueError("update work/current.md before checkpointing")
        if fingerprint(root) != before:
            raise ValueError("files changed during checkpoint validation")
        state["checkpoint"] = {"tree": before, "handover": hashlib.sha256(handover.read_bytes()).hexdigest()}
        atomic(file, json.dumps(state, sort_keys=True) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["checkpoint"])
    parser.add_argument("--session", required=True, type=session_id)
    parser.add_argument("--base", help="the branch this work merges into; required under git")
    parser.add_argument("--verify", action="store_true", required=True)
    args = parser.parse_args()
    try:
        checkpoint(ROOT, args.session, args.base)
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        parser.exit(1, f"Checkpoint refused: {error}\n")
    print("Checkpoint: PASS")


if __name__ == "__main__":
    main()
