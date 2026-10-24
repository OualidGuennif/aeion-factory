#!/usr/bin/env python3
# Spec: knowledge/policies/security.md
"""PreToolUse hook on Read, Edit, Write and Grep: refuses to open a secret file (exit 2)."""
import json
import re
import sys
from pathlib import PurePosixPath

TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist", "env.example.local"}
SECRET_NAMES = {"auth.json", "credentials", "credentials.json", "id_rsa", "id_ed25519", "env.local"}

def deny(reason):
    print(f"Blocked by .claude/hooks/guard-path.py: {reason} (knowledge/policies/security.md).", file=sys.stderr)
    sys.exit(2)


try:
    event = json.load(sys.stdin)
except (ValueError, OSError):
    deny("the hook input could not be read; refusing rather than guessing")
if not isinstance(event, dict) or not isinstance(event.get("tool_input"), dict):
    deny("the hook event must contain a tool_input object")
tool_input = event["tool_input"]
path = tool_input.get("file_path", tool_input.get("path"))
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
sys.exit(0)
