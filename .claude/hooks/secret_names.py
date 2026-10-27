# Spec: knowledge/policies/security.md
"""The one list of secret file names that the guards, checks and analyses never open."""
import re

TEMPLATES = {".env.example", ".env.sample", ".env.template", ".env.dist", "env.example.local"}
NAMES = {"auth.json", "credentials", "credentials.json", "env.local", "id_rsa", "id_ed25519", "id_ecdsa", "id_dsa",
         ".netrc", ".npmrc", ".pypirc", ".pgpass", ".envrc"}
SUFFIXES = (".pem", ".key", ".p12", ".pfx")


def is_secret(name):
    if name in TEMPLATES:
        return False
    return bool(re.fullmatch(r"\.env(\..+)?", name)) or name in NAMES or name.endswith(SUFFIXES)
