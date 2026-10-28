# Spec: knowledge/operations/build-and-test.md
"""The project's files: from git when the folder is a repository, from the file system otherwise.

Many people run Æion Factory in a plain folder, so no check may require git just to list files."""
import os
import subprocess
from pathlib import Path

# Never walked without git: version control, dependencies, caches and local state.
SKIPPED = {".git", ".aeion", "node_modules", "vendor", ".venv", "venv", "__pycache__", ".mypy_cache", ".pytest_cache"}


def git_active(root):
    """True inside a git work tree; a broken repository (a .git git cannot read) is an error, not a plain folder."""
    try:
        result = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, capture_output=True,
                                text=True, check=False)
    except OSError:
        result = None
    active = result is not None and result.returncode == 0 and result.stdout.strip() == "true"
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
        folders[:] = [name for name in folders if name not in SKIPPED]
        relative = Path(folder).relative_to(root)
        paths += [(relative / name).as_posix() for name in files]
    return sorted(paths)
