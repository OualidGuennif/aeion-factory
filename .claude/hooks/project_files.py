# Spec: knowledge/operations/build-and-test.md
"""The project's files: from git when the folder is a repository, from the file system otherwise.

Many people run Æion Factory in a plain folder, so no check may require git just to list files."""
import os
import subprocess
from pathlib import Path

# Never walked without git, at any depth: version control, installed dependencies, caches and local state.
SKIPPED = {".git", ".aeion", "node_modules", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache", ".tox",
           ".terraform"}
# Skipped at the project root only: build output and vendored code there, a source folder of that name deeper.
TOP_SKIPPED = {"vendor", "dist", "build", "target", "out", "coverage", "htmlcov", "env", ".next", ".cache", ".gradle"}
# Files the desktop rewrites on its own: listed, they would change the project between two reads.
SKIPPED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def git_active(root):
    """True when the root is its own git work tree; a broken repository (a .git git cannot read) is an error.

    A plain folder nested inside another repository is not that repository: its files are not tracked there,
    so git would list none of them."""
    try:
        result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree", "--show-prefix"], cwd=root,
                                capture_output=True, text=True, check=False)
    except OSError:
        result = None
    # An empty prefix means the root is the top level; it also holds when the path's letter case differs.
    lines = result.stdout.split("\n") if result is not None and result.returncode == 0 else []
    active = len(lines) >= 2 and lines[0] == "true" and lines[1] == ""
    if not active and (Path(root) / ".git").exists():
        raise subprocess.CalledProcessError(result.returncode if result else 127, "git rev-parse")
    return active


def git_files(root, *args):
    """Relative paths from one git ls-files call; a failure is an error, never an empty project."""
    # check=True: the hooks that catch SubprocessError already fail closed on it.
    result = subprocess.run(["git", "ls-files", "-z", *args], cwd=root, capture_output=True, check=True)
    return [os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw]


def project_files(root, untracked=False):
    """Sorted relative paths: tracked files (plus untracked, unignored ones when asked) under git, else a walk."""
    root = Path(root)
    if git_active(root):
        paths = git_files(root)
        if untracked:
            paths += git_files(root, "--others", "--exclude-standard")
        return sorted(set(paths))
    paths = []
    # os.walk does not follow directory symlinks, so the walk stays inside the project.
    for folder, folders, files in os.walk(root):
        top = Path(folder) == root
        folders[:] = [name for name in folders if name not in SKIPPED and not (top and name in TOP_SKIPPED)]
        relative = Path(folder).relative_to(root)
        paths += [(relative / name).as_posix() for name in files if name not in SKIPPED_FILES]
    return sorted(paths)
