# Spec: knowledge/components/framework-mode.md
"""The owner's per-clone settings, read the same way by every hook and tool.

.aeion/settings.json (ignored local state, with or without git) holds two keys:
  doc_gate   "enforce" (the default), "warn" or "off": what the doc gate does before an edit
  framework  the aeion-framework API address; its presence is what turns framework mode on
AEION_FRAMEWORK_URL overrides the address for one process tree (CI, a container, a sandbox), and
AEION_FRAMEWORK_TOKEN, never stored, is sent to a gateway in front of the service.
A file that cannot be read fails closed: the gate enforces and framework mode is off."""
import json
import os
import re
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

from project_files import git_active, project_files

SETTINGS = ".aeion/settings.json"
HEALTH_CACHE = ".aeion/framework-health.json"
GATES = ("enforce", "warn", "off")
# The aeion-framework releases this template is written against: from 1.1 up to, not including, 2.0.
# The tech-watch moves both values once a newer release is read and tested.
SUPPORTED = ((1, 1), (2, 0))
TESTED = "1.1.9"
HEALTH_SECONDS = 600
# aeion-framework's code annotation: a comment naming the requirement a line implements.
REQ = re.compile(r"@req\s+([A-Z][A-Z0-9_]*-[0-9]{3,6})\b")
REQ_GIT = r"@req[[:space:]]+[A-Z][A-Z0-9_]*-[0-9]{3,6}"
REQUEST_SECONDS = 3


def load(root):
    """(settings, problem or None); a missing file is an empty, valid one."""
    path = Path(root) / SETTINGS
    if not path.exists():
        return {}, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return {}, f"{SETTINGS} is unreadable ({type(error).__name__}): the doc gate enforces and framework mode is off"
    if not isinstance(data, dict):
        return {}, f"{SETTINGS} is not a JSON object: the doc gate enforces and framework mode is off"
    return data, None


def save(root, data):
    """Write the settings whole: beside the old file, then swapped, so no reader sees half a file."""
    path = Path(root) / SETTINGS
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, prefix=".settings-", suffix=".json")
    with os.fdopen(handle, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


def doc_gate(root):
    """(mode, problem or None): enforce unless the owner chose warn or off in a readable file."""
    data, problem = load(root)
    if problem:
        return "enforce", problem
    mode = data.get("doc_gate", "enforce")
    if mode not in GATES:
        return "enforce", f"{SETTINGS} doc_gate {mode!r} is not one of {', '.join(GATES)}: the gate enforces"
    return mode, None


def address_problem(url):
    """Why url cannot be a framework address, or None."""
    if not isinstance(url, str) or not url.strip() or len(url) > 2048:
        return "the address must be a nonempty string"
    parts = urlsplit(url.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return "the address must be an http:// or https:// URL with a host"
    if parts.username or parts.password:
        return "the address must not carry credentials; a gateway token goes in AEION_FRAMEWORK_TOKEN"
    if parts.query or parts.fragment:
        return "the address must not carry a query or a fragment"
    return None


def framework(root):
    """(address or None, source "env" | "file" | None, problem or None). No address: mode off."""
    env = os.environ.get("AEION_FRAMEWORK_URL")
    if env:
        problem = address_problem(env)
        return (None, "env", f"AEION_FRAMEWORK_URL: {problem}") if problem else (env.strip().rstrip("/"), "env", None)
    data, problem = load(root)
    if problem:
        return None, "file", problem
    url = data.get("framework")
    if url is None:
        return None, None, None
    problem = address_problem(url)
    if problem:
        return None, "file", f"{SETTINGS} framework: {problem}; framework mode is off"
    return url.strip().rstrip("/"), "file", None


def supported(version):
    """Whether an aeion-framework version is inside the supported range."""
    try:
        major, minor = (int(part) for part in str(version).split("-")[0].split(".")[:2])
    except ValueError:
        return False
    return SUPPORTED[0] <= (major, minor) < SUPPORTED[1]


def request(url, timeout=REQUEST_SECONDS):
    """GET url as JSON: (status, body or None). The gateway token, when set, travels in a header."""
    headers = {"Accept": "application/json, application/problem+json"}
    token = os.environ.get("AEION_FRAMEWORK_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=timeout) as answer:
            status, raw = answer.status, answer.read(1_048_576)
    except urllib.error.HTTPError as error:
        try:
            status, raw = error.code, error.read(65_536)
        finally:
            error.close()
    try:
        return status, json.loads(raw.decode("utf-8")) if raw else None
    except (UnicodeDecodeError, ValueError):
        return status, None


def health(url, timeout=REQUEST_SECONDS):
    """(version or None, problem or None) from the service's readiness probe; unknown is never ready."""
    try:
        status, body = request(f"{url}/health/ready", timeout)
    except (OSError, ValueError) as error:
        return None, f"{url} is unreachable ({type(error).__name__})"
    if status != 200 or not isinstance(body, dict):
        return None, f"{url}/health/ready answered {status}, not a ready service"
    version = body.get("version")
    if not isinstance(version, str) or not supported(version):
        low, high = SUPPORTED
        return None, (f"{url} runs aeion-framework {version!r}; this template supports "
                      f"{low[0]}.{low[1]} up to {high[0]}.{high[1]} (tested {TESTED})")
    return version, None


def cached_health(root, url, now=None):
    """health(), remembered for ten minutes so a session start never waits on the network twice."""
    now = time.time() if now is None else now
    path = Path(root) / HEALTH_CACHE
    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
        if cached.get("url") == url and 0 <= now - cached.get("at", -HEALTH_SECONDS) < HEALTH_SECONDS:
            return cached.get("version"), cached.get("problem")
    except (OSError, ValueError, AttributeError):
        pass
    version, problem = health(url)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"url": url, "at": now, "version": version, "problem": problem}), encoding="utf-8")
    except OSError:
        pass
    return version, problem


def annotated(root, limit=5000):
    """Whether the project's code names aeion-framework requirements (@req ID). Markdown and the passive
    skills pool are prose, never annotations. An unreadable tree answers no: this only drives a hint."""
    root = Path(root)
    try:
        if git_active(root):
            done = subprocess.run(["git", "grep", "-qIE", REQ_GIT, "--", ".", ":!*.md", ":!skills/"],
                                  cwd=root, capture_output=True, timeout=5)
            return done.returncode == 0
        for count, relative in enumerate(project_files(root)):
            if count >= limit:
                return False
            if relative.endswith(".md") or relative.startswith("skills/"):
                continue
            try:
                with open(root / relative, "rb") as stream:
                    if REQ.search(stream.read(65_536).decode("utf-8", "ignore")):
                        return True
            except OSError:
                continue
    except (OSError, subprocess.SubprocessError):
        return False
    return False
