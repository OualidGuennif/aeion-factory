#!/usr/bin/env python3
# Spec: knowledge/components/doc-gate.md
"""The doc gate: the docs covering a file are read in the session before the file is edited.

SessionStart  forgets what was read, except at startup: after a compaction or a resume the text is gone.
PostToolUse   remembers each doc the session read (the Read tool, or a shell reader on its path) or
              wrote; in warn mode, after an edit, names the docs it skipped, once per file.
PreToolUse    in enforce mode, refuses an Edit, MultiEdit, Write or NotebookEdit of a file whose covering
              docs (tools/knowledge/doc-links --for, or the Spec: header a new file carries) were not all read.
Docs, knowledge/ and work/ are never gated. Exit 2 refuses; exit 0 allows."""
import json
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / ".claude/hooks"))
import aeion_settings  # noqa: E402

EDITS = {"Edit", "MultiEdit", "Write", "NotebookEdit"}
# Shell programs whose file arguments are read: a harness without a Read tool reads through these.
READERS = {"cat", "head", "tail", "sed", "less", "more", "bat", "nl"}
OPERATORS = set("();&|<>")
SPEC = re.compile(r"\bSpec:\s*(knowledge/[\w./-]+\.md)")
LOOKUP_SECONDS = 2
SWITCH = "The owner switches the gate with tools/aeion-settings doc-gate warn|off."


def deny(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)


def state(session, kind):
    return Path(tempfile.gettempdir()) / f"claude-doc-{kind}-{session}"


def remembered(session, kind):
    try:
        return set(state(session, kind).read_text(encoding="utf-8").splitlines())
    except OSError:
        return set()


def remember(session, kind, paths):
    if paths:
        with state(session, kind).open("a", encoding="utf-8") as stream:
            stream.write("".join(path + "\n" for path in paths))


def inside(raw, base):
    """The project-relative path of raw, or None outside the project."""
    if not isinstance(raw, str) or not raw or "\0" in raw:
        return None
    path = Path(raw).expanduser()
    path = (path if path.is_absolute() else base / path).resolve()
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else None


def gated(rel):
    return not (rel.startswith(("knowledge/", "work/")) or rel.lower().endswith(".md"))


def covering(rel, data, tool):
    """The docs covering rel, or None when they cannot be listed. A Write of a new file brings its own Spec: header."""
    try:
        done = subprocess.run([sys.executable, str(ROOT / "tools/knowledge/doc-links"), "--for", rel], cwd=ROOT,
                              capture_output=True, text=True, timeout=LOOKUP_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return None
    if done.returncode:
        return None
    docs = {line for line in done.stdout.splitlines() if line}
    if tool == "Write" and isinstance(data.get("content"), str):
        head = "\n".join(data["content"].split("\n", 30)[:30])
        docs |= {doc for doc in SPEC.findall(head) if (ROOT / doc).is_file()}
    return sorted(docs)


def shell_reads(command, base):
    """The .md files inside the project that a shell command hands to a reader."""
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        words = list(lexer)
    except ValueError:
        return []
    reads, program = [], None
    for word in words:
        if word and set(word) <= OPERATORS:
            program = None
        elif program is None:
            program = Path(word).name
        elif program in READERS and word.lower().endswith(".md") and not word.startswith("-"):
            rel = inside(word, base)
            if rel and (ROOT / rel).is_file():
                reads.append(rel)
    return reads


def edited(data):
    return data.get("file_path", data.get("notebook_path"))


try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    event = None
if not isinstance(event, dict):
    deny("Doc gate: the hook input is unreadable, so the edit cannot be checked. " + SWITCH)
name, tool = event.get("hook_event_name"), event.get("tool_name")
data = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
session = event.get("session_id")
valid = isinstance(session, str) and bool(session) and not any(char in session for char in "/\\\0")
base = Path(event["cwd"]) if isinstance(event.get("cwd"), str) and event["cwd"] else ROOT

# A compacted, resumed or cleared context no longer holds what was read. A startup is a new session
# with nothing remembered yet, and OpenCode sends one before every prompt, which must not empty the set.
if name == "SessionStart":
    if valid and event.get("source") != "startup":
        for kind in ("read", "warned"):
            state(session, kind).unlink(missing_ok=True)
    sys.exit(0)

if name == "PostToolUse" and valid:
    if tool == "Read":
        rel = inside(data.get("file_path", data.get("filePath", data.get("path"))), base)
        if rel and rel.lower().endswith(".md"):
            remember(session, "read", [rel])
    elif tool == "Bash" and isinstance(data.get("command"), str):
        workdir = data.get("workdir", data.get("cwd"))
        remember(session, "read", shell_reads(data["command"], Path(workdir) if isinstance(workdir, str) else base))
    elif tool in EDITS:
        rel = inside(edited(data), base)
        if rel and rel.lower().endswith(".md"):
            # A doc the agent wrote or changed is a doc it has in front of it.
            remember(session, "read", [rel])
        elif rel and gated(rel) and aeion_settings.doc_gate(ROOT)[0] == "warn" and rel not in remembered(session, "warned"):
            unread = [doc for doc in covering(rel, data, tool) or [] if doc not in remembered(session, "read")]
            if unread:
                remember(session, "warned", [rel])
                print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext":
                    f"Doc gate (warn): {rel} was edited before reading {', '.join(unread)}; read it and check the edit against it."}}))
    sys.exit(0)

if name != "PreToolUse" or tool not in EDITS or aeion_settings.doc_gate(ROOT)[0] != "enforce":
    sys.exit(0)
rel = inside(edited(data), base)
if rel is None or not gated(rel):
    sys.exit(0)
docs = covering(rel, data, tool)
if docs is None:
    deny(f"Doc gate: the docs covering {rel} could not be listed (tools/knowledge/doc-links --for failed or took "
         f"over {LOOKUP_SECONDS} seconds), so the edit is refused. {SWITCH}")
if docs and not valid:
    deny(f"Doc gate: {rel} is covered by {', '.join(docs)}, and this event has no valid session to remember reads in. {SWITCH}")
unread = [doc for doc in docs if doc not in remembered(session, "read")] if docs else []
if unread:
    deny(f"Doc gate: read {', '.join(unread)} before editing {rel}; {'it covers' if len(unread) == 1 else 'they cover'} "
         f"this file. Use the Read tool or a bounded shell read (sed -n 1,200p {unread[0]}), then edit again. {SWITCH}")
sys.exit(0)
