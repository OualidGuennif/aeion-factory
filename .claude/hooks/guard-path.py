#!/usr/bin/env python3
# Spec: knowledge/policies/security.md
"""Refuse secret paths and unbounded large reads before native tool execution (exit 2)."""
import json
import re
import sys
from pathlib import Path, PurePosixPath

TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist", "env.example.local"}
SECRET_NAMES = {"auth.json", "credentials", "credentials.json", "id_rsa", "id_ed25519", "env.local"}
MAX_INTAKE_BYTES, MAX_INTAKE_LINES = 65536, 400
MAX_SCAN_BYTES = 1024 * 1024
INTAKE_REASON = ("bounded intake: use a Read window of at most 400 lines, head -c 65536, "
                 "or a targeted search with a positive result limit (knowledge/policies/bounded-intake.md)")

def deny(reason):
    print(f"Blocked by .claude/hooks/guard-path.py: {reason} (knowledge/policies/security.md).", file=sys.stderr)
    sys.exit(2)


def check_intake(path, tool, data):
    if tool not in {"Read", "Grep"} or not path:
        return
    target = Path(path)
    try:
        if not target.exists() or target.is_dir():
            return
        if not target.is_file():
            deny(INTAKE_REASON)
        if tool == "Grep":
            limit = data.get("head_limit", data.get("limit"))
            if data.get("output_mode") in {"count", "files_with_matches"} or (type(limit) is int and 0 < limit <= MAX_INTAKE_LINES):
                return
            limit, offset = None, 1
        else:
            limit, offset = data.get("limit"), data.get("offset", 1)
        bounded = type(limit) is int and 0 < limit <= MAX_INTAKE_LINES
        if type(offset) is not int or offset < 1:
            deny(INTAKE_REASON)
        if not bounded and target.stat().st_size > MAX_INTAKE_BYTES:
            deny(INTAKE_REASON)
        scanned, total, count = 0, 0, 0
        with target.open("rb") as stream:
            for index in range(offset - 1 + (limit if bounded else MAX_INTAKE_LINES + 1)):
                line = stream.readline(MAX_SCAN_BYTES - scanned + 1)
                if not line:
                    break
                scanned += len(line)
                if scanned > MAX_SCAN_BYTES:
                    deny(INTAKE_REASON)
                if index >= offset - 1:
                    total, count = total + len(line), count + 1
                    if total > MAX_INTAKE_BYTES or count > MAX_INTAKE_LINES:
                        deny(INTAKE_REASON)
    except OSError:
        deny("the intake size could not be verified; " + INTAKE_REASON)


try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    deny("the hook input could not be read; refusing rather than guessing")
if not isinstance(event, dict) or not isinstance(event.get("tool_input"), dict):
    deny("the hook event must contain a tool_input object")
tool_input = event["tool_input"]
path = tool_input.get("file_path", tool_input.get("filePath", tool_input.get("path")))
if path is None and event.get("tool_name") == "Grep":
    path = ""
elif not isinstance(path, str) or (not path and event.get("tool_name") != "Grep"):
    deny("the tool path must be a nonempty string")
if "\0" in path:
    deny("the tool path contains a null byte")
name = PurePosixPath(path).name
if name not in TEMPLATES and (bool(re.fullmatch(r"\.env(\..+)?", name)) or name in SECRET_NAMES
                              or name.endswith((".pem", ".key"))):
    print(f"Blocked by .claude/hooks/guard-path.py: {name} holds secrets and is never opened "
          f"(knowledge/policies/security.md).", file=sys.stderr)
    sys.exit(2)
check_intake(path, event.get("tool_name", "Read"), tool_input)
sys.exit(0)
