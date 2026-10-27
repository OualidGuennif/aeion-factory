# Spec: knowledge/policies/security.md
"""The one list of secret file names that the guards, checks and analyses never open."""
import fnmatch
import re

TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist", "env.example.local"}
NAMES = {"auth.json", "credentials", "credentials.json", "env.local", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
         ".netrc", ".npmrc", ".pypirc", ".pgpass", ".envrc"}
SUFFIXES = (".pem", ".key", ".p12", ".pfx")
DOTFILES = sorted({name for name in NAMES if name.startswith(".")} | {".env", ".env.local"})
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


def dotfile_secrets(pattern):
    """The dotfile secrets a glob's last part names wherever it expands; none unless it starts with a literal dot."""
    if not re.match(r"\.[^*?.]", pattern):
        return set()
    return {name for name in DOTFILES if fnmatch.fnmatchcase(name, pattern)}
