#!/usr/bin/env python3
"""Fixture tests for tools/knowledge/knowledge-check: a throwaway root, the real tool run with --root.

Run with: python3 tools/knowledge/tests/test_knowledge_check.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

TOOL = Path(__file__).resolve().parents[1] / "knowledge-check"
FIELDS = "- Owner decision: x\n- State: x\n- Next: x (who: agent)\n- Blocker: none\n- Evidence: x\n"
failures, passes = [], 0


def check(name, current, want_code, want_text=""):
    global passes
    root = Path(tempfile.mkdtemp())
    (root / "work").mkdir()
    (root / "work/current.md").write_text("# Current work\n\n" + current)
    r = subprocess.run([sys.executable, str(TOOL), "--root", str(root)], capture_output=True, text=True)
    if r.returncode == want_code and want_text in r.stdout:
        passes += 1
    else:
        failures.append(f"{name}: exit {r.returncode}, stdout {r.stdout!r}")


check("a complete entry passes", "## A task — ACTIVE\n" + FIELDS, 0, "PASS")
# A missing field names itself and the whole shape, so the next entry is written right (Pi FB-001).
check("a missing field is named", "## A task — ACTIVE\n- State: x\n", 1, "lacks '- Owner decision:'")
check("a missing field prints the shape", "## A task — ACTIVE\n- State: x\n", 1,
      "an entry is '## <title> — <STATUS>' then the lines - Owner decision: / - State: / - Next: / - Blocker: / - Evidence:")
check("an entry over 10 lines", "## A task — ACTIVE\n" + FIELDS + "- more\n" * 6, 1, "over 10 lines")

for f in failures:
    print("FAIL:", f)
print(f"{passes} passed, {len(failures)} failed")
sys.exit(1 if failures else 0)
