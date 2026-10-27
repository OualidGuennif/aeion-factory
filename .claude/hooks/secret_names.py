# Spec: knowledge/policies/security.md
"""The one list of secret file names that the guards, checks and analyses never open."""
import fnmatch
import re

TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist", "env.example.local"}
NAMES = {"auth.json", "credentials", "credentials.json", "env.local", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
         ".netrc", ".npmrc", ".pypirc", ".pgpass", ".envrc"}
SUFFIXES = (".pem", ".key", ".p12", ".pfx")
BRACES = re.compile(r"\{[^{}]*(,|\.\.)[^{}]*\}")


def is_secret(name):
    if name in TEMPLATES:
        return False
    return bool(re.fullmatch(r"\.env(\..+)?", name)) or name in NAMES or name.endswith(SUFFIXES)


def brace_variants(word):
    """The words bash brace expansion makes of word; a sequence ({a..z}) widens to a wildcard."""
    match = BRACES.search(word)
    if not match:
        return [word]
    inner = match.group(0)[1:-1]
    options = inner.split(",") if "," in inner else ["*"]
    variants = [v for option in options for v in brace_variants(word[:match.start()] + option + word[match.end():])]
    if len(variants) > 256:
        raise ValueError("too many brace variants to verify")
    return variants


EXAMPLES = sorted(NAMES | {".env", ".env.local", "key.pem", "server.key", "cert.p12", "cert.pfx"})
# Ordinary files that a generic glob (*, *.json, c*, *_*, .*) also matches; none shares a secret's stem.
ORDINARY = ("README.md", "main.py", "test_main.py", "package.json", "config.yml", "index.js", "app.tsx",
            "data", "docs", "go.sum", "Makefile", "notes.txt", "eslint.config.js", "setup.py",
            "kustomization.yaml", "build.gradle.kts")
DOT_ORDINARY = (".git", ".github", ".gitignore", ".editorconfig", ".vscode", ".claude")


def shell_pattern(pattern):
    """The glob as Python's fnmatch and glob read it: bash, zsh and ripgrep take [^x] for [!x]."""
    return pattern.replace("[^", "[!")


def named_secrets(pattern):
    """The secrets a glob's last part names wherever it expands: a dotfile glob with a literal first
    letter (.e*) by its name; any other glob when it matches a secret and no ordinary name, so *.json
    and .* stay allowed and id_* and .*rc do not."""
    pattern = shell_pattern(pattern)
    if pattern.startswith(".."):
        return set()
    dotted = pattern.startswith(".")
    secrets = {n for n in EXAMPLES if n.startswith(".") == dotted and fnmatch.fnmatchcase(n, pattern)}
    ordinary = DOT_ORDINARY if dotted else ORDINARY
    if re.match(r"\.[^*?.]", pattern) or not any(fnmatch.fnmatchcase(n, pattern) for n in ordinary):
        return secrets
    return set()
