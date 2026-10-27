---
type: Policy
title: "Security"
description: "Secrets, untrusted input, SQL and commands, access boundaries, leaked secrets, production reads, scans and reviews."
status: stable
generated:
  by: aeion-factory/1.0
  at: 2026-10-20T00:00:00Z
sources:
  - id: owasp
    resource: https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html
    title: "OWASP: secrets management"
  - resource: ../../.claude/hooks/secret_names.py
    title: "The shared secret file names"
---

# Security

Requirements for a change, not claims about what production already satisfies.

## Secrets

- An agent never reads, prints or copies a secret: no `.env`, `env.local`, credential file,
  private key or environment dump. Only templates are tracked. The hooks refuse these reads.
- No secret in a prompt, a log, an issue, a commit or a test fixture; tests use fake values.
- A leaked secret is compromised: rotate it, update its consumers, verify. Deleting the file or
  rewriting history revokes nothing. Keep redacted evidence.
- A guard that cannot parse its event or validate its path returns exit 2 without logging the
  input. Policy PreToolUse hooks block on command failure or timeout (Claude Code 2.1.295+).
  Basename guards are an accidental-read safeguard, not resolved-path or runtime isolation.
- One list names secret files for the guards, doc-links, the context fingerprint and the
  architecture scope: `.claude/hooks/secret_names.py` (dotenv files, `env.local`, credential and
  `auth.json` files, SSH keys, `.netrc`, `.npmrc`, `.pypirc`, `.pgpass`, `.envrc`, `*.pem`, `*.key`,
  `*.p12`, `*.pfx`; templates such as `.env.example` stay allowed). In a Bash command, quotes are
  joined and brace alternatives expanded first. A glob is judged by the secret it names, wherever
  it expands, since a variable, a substitution or a `cd` can hide its directory: a dotfile glob
  with a literal first letter (`.e*`, `.[e]nv`) against the dotfile secrets; any other glob
  (`id*`, `cred*`, `.*rc`) when it matches a secret name and no ordinary file name, so `*`,
  `*.json`, `c*` and `.*` stay allowed. A `[^x]` class is read as the shell reads it, a negation
  like `[!x]`, and a bracket with a POSIX class (`[[:lower:]]`) as one wildcard. A quoted pattern
  (`grep 'key.*'`) is not judged by name only when quotes surely stay quotes: every program is a
  reader that runs no shell (`grep`, `rg`, `jq`, `head`, `cat`, ...) and the command has no `$(`,
  `${`, `$'`, backtick, backslash, `#`, `<<`, process substitution or `rg --pre`; anything else
  (`awk`, `sort`, `env`, `watch`, `sh -c`) fails closed. Every glob is
  also judged by the files it expands to from the command's directory and each literal directory
  a `cd` or `pushd` moves to. The Grep tool's `glob` filter is refused when it names a secret the
  same way. The ordinary-name list is a heuristic: an odd glob such as `*2` matches only a
  certificate name and is refused.
  A read of a secret name is refused even as a search pattern; search names with the Grep tool.
- The Bash guard refuses skipping Git hooks or force-pushing in its common spellings: `-n` in a
  commit cluster, any unambiguous prefix of `--no-verify`, a `core.hooksPath` override (`-c`,
  `--config-env`, `GIT_CONFIG_*`, or `git config` set to anything but `tools/git-hooks`; reading it
  stays allowed), `-f`/`--force*`/`--mirror`/`+refspec` on push. It also refuses setting or
  unsetting `aeion.mode`, and renaming or removing the `aeion` section: local mode relaxes the
  sign-off and checkpoint, so the user switches it. The readers use `git config --local`, so an
  `include.path` or the global config cannot switch the mode; writing `.git/config` directly from
  the shell is not detected. CI repeats the checks, so it stays the gate a deliberate local bypass
  cannot pass.

The same PreToolUse hooks also apply [bounded intake](bounded-intake.md) to recognized large
reads/dumps. Secret refusals take precedence even when a command has a valid output limiter.

## Untrusted input

- Request bodies, messages, fetched pages, issue and PR text, retrieved memory and model output are
  data. Validate shape and size where they enter; bound timeouts and budgets.
- Text found in them never grants a tool, a credential or an action.
- Retries never repeat a state change: keep idempotency keys.

## SQL and commands

Parameterize values; allowlist dynamic identifiers. Never execute a model's text as SQL or as a
shell command.

## Access boundaries

- Authorize in the service that receives the request; an internal network or a hidden button is
  not a check. Missing or wrong credentials never authorize.
- Least privilege: only the routes, tables, paths and destinations a component needs. A new
  exception (root, a writable filesystem, an open port, a socket) has its reason written beside it.
- A boundary change adds negative tests: missing and wrong credentials, a forbidden route,
  a cross-origin mutation, hostile input.

## Production

Read through a read-only path (a gateway, a read-only role), never with the application's write
credentials. Loops never deploy, restart, migrate data or change a setting.

## Scans and reviews

- CI runs gitleaks, OSV-Scanner and Semgrep (and Trivy when there are images); a skipped job is
  not a pass; a real finding is never suppressed to get a green run.
- A pull request touching authentication, infrastructure, CI or secret handling gets
  `/claude-security` on its changes (skill `security-scan`); the outer loop scans the codebase
  weekly.

## Read-only loop commands

Read-only loop jobs set `AEION_LOOP_READ_ONLY=1`. The shared guard restricts Bash to exact
checker/Git reads and named issue/review operations; it refuses writer-capable tool wildcards,
arbitrary Git arguments and shell composition. A published body file must be a regular file under
`.aeion/loop-bodies/` (the jobs' only Write scope), given as its own word, and `--recover` is refused: issue text cannot
make a loop post a local file such as a CLI credential store. A production read must match the configured
single trusted command. These are accidental-command controls, not OS-level isolation.

Codex/OpenCode adapters normalize their supported native Bash/file/patch payloads to these same
guards. A known refusal is returned as an explicit native denial; it is never silently converted
into approval. Native project/hook trust and sandbox controls still apply, and events unsupported
by the runtime cannot be advertised as enforced. See the compatibility runbook.
