#!/usr/bin/env python3
# Spec: knowledge/policies/security.md
"""PreToolUse hook on Bash: blocks commands that would expose a secret or bypass a guard.

Input: the hook event as JSON on stdin; tool_input.command is the command. Output: exit 2 with the
reason on stderr blocks it; a JSON "ask" decision asks a human; exit 0 lets it run. A seatbelt,
not a guarantee: the rules are in knowledge/policies/security.md.
"""
import glob
import json
import os
import re
import shlex
import sys
from pathlib import Path, PurePosixPath
from secret_names import brace_variants, is_secret, named_secrets, shell_pattern

READERS = {"cat", "less", "more", "head", "tail", "grep", "rg", "awk", "sed", "strings", "base64",
           "xxd", "od", "source", ".", "cp", "scp", "rsync", "jq", "python3", "python", "node", "vim", "nano"}
MAX_INTAKE_BYTES, MAX_INTAKE_LINES = 65536, 400
LOOP_BODIES = ".aeion/loop-bodies/"
INTAKE_REASON = ("bounded intake: replace the dump with head -n 80, head -c 65536, "
                 "a targeted rg search or a summary; keep a limiter last in its own pipeline "
                 "(knowledge/policies/bounded-intake.md).")


def deny(reason):
    print(f"Blocked by .claude/hooks/guard-bash.py: {reason}", file=sys.stderr)
    sys.exit(2)


def ask(reason):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                             "permissionDecisionReason": reason}}))
    sys.exit(0)


def directories(command, base):
    """The directories a glob in the command may expand in: its own and each literal one a cd moves to."""
    current, found = base, [base]
    for words in simple_commands(command):
        words = program(words)
        if words and words[0] == "<script>":
            found += directories(words[1], current)
        elif words and PurePosixPath(words[0]).name in ("cd", "pushd"):
            target = next((w for w in words[1:] if not w.startswith("-")), "~")
            current = os.path.join(current, os.path.expanduser(target))
            found.append(current)
    return found


def mentioned_secrets(tokens, shell_tokens, bases, unquoted_globs):
    names = {PurePosixPath(t).name for t in tokens if is_secret(PurePosixPath(t).name)}
    # Only the shell expands braces and globs; a heredoc body fed to a program is text.
    for token, unquoted in zip(shell_tokens, unquoted_globs):
        for word in brace_variants(token):
            name = PurePosixPath(word).name
            if is_secret(name):
                names.add(name)
            elif any(char in word for char in "*?["):
                # A glob is judged by the secret it names wherever it expands, since a variable, a command
                # substitution or a cd can hide its directory; and by the files it expands to here. A
                # quoted pattern ('key.*') is a regex or prose the shell never expands, so only the files.
                if unquoted:
                    names |= named_secrets(name)
                pattern = shell_pattern(os.path.expanduser(word))
                for base in bases:
                    matches = glob.glob(pattern, root_dir=None if os.path.isabs(pattern) else base)
                    names |= {PurePosixPath(m).name for m in matches if is_secret(PurePosixPath(m).name)}
    return sorted(names)


# Environment dumps hold keys. The command is split into simple commands (newlines, ; & | && || and
# parentheses outside quotes; redirections dropped; heredoc bodies only when a shell reads them);
# wrappers are unwrapped (sudo, time, xargs, nohup, docker [compose] exec/run, kubectl exec, ssh,
# sh -c/-lc, su -c, shell keywords,
# recursively); then refused: printenv; env with no program to run;
# declare, typeset, export and set that print variables; ps with BSD e or -E (process environments). And
# anywhere in the command: the words environ, environb and ENVIRON; an interpreter together with
# process.env, Deno.env or ENV; jq with env or $ENV. A seatbelt: search for these names with the
# Grep tool, and put prose that names them in a file.
ENV_WORD = re.compile(r"\b(environ|environb|ENVIRON)\b")
INTERPRETER = re.compile(r"\b(python3?|node|deno|bun|tsx|ts-node|npx|ruby|perl)\b")
ENV_IN_CODE = re.compile(r"process\.env\b|Deno\.env\b|%ENV\b|\bENV\b")
JQ_ENV = re.compile(r"\bjq\b.*(\benv\b|\$ENV\b)", re.S)
SEPARATOR_CHARS, REDIRECT_CHARS = set(";&|()\n"), set("<>&")
WRAPPERS = {"sudo", "doas", "time", "nohup", "nice", "xargs", "command", "builtin", "exec", "watch",
            "timeout", "stdbuf", "setsid", "chroot"}
DOCKER_VALUE_FLAGS = {"-u", "--user", "-e", "--env", "-w", "--workdir", "--env-file", "--detach-keys",
                      "-v", "--volume", "--network", "--entrypoint", "-p", "--publish", "--name", "-l",
                      "--label", "--mount", "--platform", "--pull", "--cpus", "-m", "--memory", "--index"}
VALUE_FLAGS = {"sudo": {"-u", "-g", "-h", "-p", "-C", "-D", "-R", "-T", "-U"},
               "docker": DOCKER_VALUE_FLAGS,
               "ssh": {"-i", "-p", "-o", "-l", "-F", "-J", "-L", "-R", "-D", "-E", "-b", "-c", "-m", "-O",
                       "-Q", "-S", "-W", "-w", "-B"},
               "ps": {"-o", "-p", "-u", "-U", "-G", "-g", "-t", "-O", "-q"},
               "env": {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"},
               "xargs": {"-n", "-I", "-i", "-L", "-l", "-P", "-s", "-d", "-E", "-a", "--max-args",
                         "--replace", "--max-lines", "--max-procs", "--delimiter", "--arg-file"},
               "timeout": {"-s", "--signal", "-k", "--kill-after"}, "nice": {"-n"}}
SHELLS = {"sh", "bash", "zsh", "dash", "ksh"}
SHELL_KEYWORDS = {"do", "then", "else", "elif", "if", "while", "until", "{", "}", "!", "time"}
DOCKER_GLOBAL_VALUE_FLAGS = {"-f", "--file", "-p", "--project-name", "--project-directory", "--context",
                             "-c", "-H", "--host", "--env-file", "--profile", "--log-level", "--config",
                             "--ansi", "--progress", "--parallel"}
HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1")
SHELL_CONSUMER = re.compile(r"\b(sh|bash|zsh|dash|ksh|ssh|exec)\b")


def without_inert_heredocs(command):
    """Drops heredoc bodies fed to anything but a shell: a script's text is not a command line."""
    out, end, keep = [], None, True
    for line in command.split("\n"):
        if end is not None:
            if keep:
                out.append(line)
            if line.strip() == end:
                end = None
            continue
        out.append(line)
        m = HEREDOC.search(line)
        if m:
            before, after = line[:m.start()], line[m.end():]
            consumer = before + (after if after.lstrip().startswith("|") else "")
            end = m.group(2)
            keep = bool(SHELL_CONSUMER.search(consumer)) and not INTERPRETER.search(consumer)
    return "\n".join(out)


def tokens_of(text):
    try:
        lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
        lexer.whitespace, lexer.whitespace_split, lexer.commenters = " \t\r", True, ""
        tokens = list(lexer)
    except ValueError:
        tokens = re.findall(r"[;&|()<>\n]+|[^\s;&|()<>]+", text)
    # A parenthesis glued to other punctuation (";)", "))", ");") stands on its own.
    out = []
    for t in tokens:
        if len(t) > 1 and set(t) <= set(";&|()<>\n") and set(t) & set("()"):
            out += [p for p in re.split(r"([()])", t) if p]
        else:
            out.append(t)
    return out


def simple_commands(command):
    current, skip_next, outer = [], False, []
    for w in tokens_of(without_inert_heredocs(command.replace("\\\n", " "))):
        chars = set(w)
        # $( ... ) is a command of its own; its value stands in the outer command.
        if w == "(" and current and current[-1].endswith("$") and not skip_next:
            current[-1] = current[-1] + "(...)"
            outer.append(current)
            current = []
            continue
        if outer and w[:1] == ")" and chars <= SEPARATOR_CHARS | REDIRECT_CHARS:
            while w[:1] == ")" and outer:
                yield current
                current = outer.pop()
                w = w[1:]
            if not w:
                continue
            chars = set(w)
        if skip_next:
            skip_next = False
        elif w and chars <= SEPARATOR_CHARS | REDIRECT_CHARS and chars & SEPARATOR_CHARS - {"&"}:
            yield current
            current = []
        elif w and chars <= REDIRECT_CHARS and chars & {"<", ">"}:
            skip_next = True
            if current and current[-1].isdigit():
                current.pop()
        elif w and chars <= {"&"}:
            yield current
            current = []
        else:
            current.append(w)
    yield current
    yield from reversed(outer)


def skip_options(words, tool):
    takes_value = VALUE_FLAGS.get(tool, set())
    while words and words[0].startswith("-"):
        flag = words.pop(0)
        if flag == "--":
            break
        if flag in takes_value and words:
            words.pop(0)
    return words


def docker_subcommand(words):
    """(subcommand, the words after it) of a docker or docker compose command line, global options skipped."""
    rest = list(words[1:])
    while rest:
        if rest[0] in ("compose", "container"):
            rest.pop(0)
        elif rest[0] in DOCKER_GLOBAL_VALUE_FLAGS and len(rest) > 1:
            rest = rest[2:]
        elif rest[0].startswith("-"):
            rest.pop(0)
        else:
            return rest[0], rest[1:]
    return None, []


CONFIG_LISTS = {"-q", "--quiet", "--services", "--volumes", "--images", "--profiles", "--networks"}


def compose_config(command):
    """docker compose config prints the configuration with the secrets filled in (-q only validates)."""
    for words in simple_commands(command):
        words = program(words)
        if words and PurePosixPath(words[0]).name in ("docker", "docker-compose", "podman"):
            sub, rest = docker_subcommand(words)
            if sub == "config" and not (CONFIG_LISTS & set(rest)):
                return True
        elif words and words[0] == "<script>" and compose_config(words[1]):
            return True
    return False


def shell_script(args):
    """The -c script of a shell's arguments (-c, -lc, -xc ...), or None."""
    for i, a in enumerate(args):
        if a.startswith("-") and not a.startswith("--") and "c" in a[1:]:
            rest = [x for x in args[i + 1:] if x != "--"]
            return rest[0] if rest else ""
    return None


def program(words):
    """The program a simple command runs, after assignments and wrappers; a nested script is checked whole."""
    words = list(words)
    while words:
        w = PurePosixPath(words[0]).name
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]) or words[0] in SHELL_KEYWORDS:
            words.pop(0)
        elif w == "command" and len(words) > 1 and words[1] in ("-v", "-V"):
            return []
        elif w in WRAPPERS:
            words = skip_options(words[1:], w)
            if w in ("timeout", "nice") and words and re.fullmatch(r"[\d.]+[smhd]?", words[0]):
                words.pop(0)
        elif w in ("docker", "docker-compose", "podman"):
            sub, rest = docker_subcommand(words)
            if sub not in ("exec", "run"):
                break
            words = skip_options(rest, "docker")[1:]
        elif w == "kubectl" and words[1:2] == ["exec"]:
            words = words[words.index("--") + 1:] if "--" in words else []
        elif w == "ssh":
            words = skip_options(skip_options(words[1:], "ssh")[1:], "ssh")
            if words:
                return ["<script>", " ".join(words)]
        elif w == "su":
            script = shell_script(words[1:])
            return ["<script>", script] if script is not None else []
        elif w in SHELLS:
            script = shell_script(words[1:])
            return ["<script>", script] if script is not None else words
        else:
            break
    return words


def prints_environment(words):
    if not words:
        return False
    name, args = PurePosixPath(words[0]).name, words[1:]
    if name == "<script>":
        return env_dump(args[0])
    if name == "printenv":
        return True
    if name == "env":
        rest = skip_options(list(args), "env")
        while rest and (re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", rest[0]) or rest[0] in ("-", "--")):
            rest.pop(0)
        rest = skip_options(rest, "env")
        return not rest
    if name in ("declare", "typeset"):
        return not args or any(a.startswith("-") and set(a[1:]) & set("xpF") for a in args)
    if name == "export":
        return not args or args == ["-p"]
    if name == "set":
        return not args
    if name == "ps":
        # BSD "e" is a letter cluster in the first argument (ps eww, ps auxe); -E is macOS's flag.
        if args and re.fullmatch(r"[a-zA-Z]+", args[0]) and "e" in args[0]:
            return True
        return any(re.fullmatch(r"-[a-zA-Z]*E[a-zA-Z]*", a) for a in args)
    return False


def env_dump(command):
    if ENV_WORD.search(command) or JQ_ENV.search(command):
        return True
    if INTERPRETER.search(command) and ENV_IN_CODE.search(command):
        return True
    return any(prints_environment(program(words)) for words in simple_commands(command))


INSPECT_DUMP_FORMAT = re.compile(r"\.Env\b|\{\{-?\s*(json\s+)?\.(Config)?\s*(\|\s*json\s*)?-?\}\}|^\s*(json)?\s*$")


def docker_inspect_dump(command):
    """docker inspect shows a container's environment unless a narrow --format leaves it out."""
    for words in simple_commands(command):
        words = program(words)
        if words and words[0] == "<script>":
            if docker_inspect_dump(words[1]):
                return True
            continue
        if not words or PurePosixPath(words[0]).name not in ("docker", "podman"):
            continue
        sub, rest = docker_subcommand(words)
        if sub != "inspect":
            continue
        fmt = None
        for i, a in enumerate(rest):
            if a in ("-f", "--format") and i + 1 < len(rest):
                fmt = rest[i + 1]
            elif a.startswith("--format="):
                fmt = a.split("=", 1)[1]
        if fmt is None or INSPECT_DUMP_FORMAT.search(fmt):
            return True
    return False


GIT_VALUE_FLAGS = {"-C", "-c", "--config-env", "--git-dir", "--work-tree", "--namespace"}
HOOKS_PATH = "tools/git-hooks"
# Short options that take a value: in a cluster, the rest is that value, not more flags.
SHORT_VALUE = {"commit": set("mFcCt"), "push": {"o"}}


def git_bypass(command):
    """The reason a git command skips the hooks or force-pushes, or None.

    Covers short clusters, +refspecs, --mirror, git's unique-prefix long options and a
    core.hooksPath override (-c, --config-env, GIT_CONFIG_* variables, or git config setting
    anything but the repository's hooks), and setting aeion.mode. Reading either stays allowed."""
    hooks_reason = "overriding core.hooksPath skips the pre-commit checks."
    for words in simple_commands(command):
        # GIT_CONFIG_* variables inject configuration into every later git run.
        if any(re.match(r"GIT_CONFIG_\w*=", w) and "core.hookspath" in w.lower() for w in words):
            return hooks_reason
        words = program(words)
        if words and words[0] == "<script>":
            reason = git_bypass(words[1])
            if reason:
                return reason
            continue
        if not words or PurePosixPath(words[0]).name != "git":
            continue
        rest = list(words[1:])
        while rest and rest[0].startswith("-"):
            flag = rest.pop(0)
            value = rest.pop(0) if flag in GIT_VALUE_FLAGS and rest else flag
            if flag.split("=", 1)[0] in ("-c", "--config-env") and "core.hookspath" in value.lower():
                return hooks_reason
        sub, args = (rest[0], rest[1:]) if rest else (None, [])
        if sub == "config":
            positional = [a for a in args if not a.startswith("-")]
            keys = [i for i, a in enumerate(positional) if a.lower() == "core.hookspath"]
            if keys:
                values = positional[keys[0] + 1:]
                unset = "unset" in positional[:keys[0]] or any(a.startswith("--unset") for a in args)
                if unset or values and values[0] != HOOKS_PATH:
                    return hooks_reason
            # Local mode relaxes the sign-off and the closure checkpoint, so only the user switches it.
            modes = [i for i, a in enumerate(positional) if a.lower() == "aeion.mode"]
            reads = {"get", "--get", "--get-all", "--get-regexp"} & set(args)
            if modes and not reads and (positional[modes[0] + 1:] or "unset" in positional[:modes[0]]
                          or any(a.startswith("--unset") for a in args)):
                return "aeion.mode is the user's switch between team and local flow; the user sets it."
            # Renaming another section to aeion (or removing it) switches the mode without naming the key.
            sections = {"--rename-section", "rename-section", "--remove-section", "remove-section"}
            if sections & set(args) and any(a.lower() == "aeion" for a in positional):
                return "aeion.mode is the user's switch between team and local flow; the user sets it."
        value_next = False
        for arg in args:
            if value_next:
                value_next = False
                continue
            if arg == "--":
                break
            name = arg.split("=", 1)[0]
            # git accepts any unambiguous prefix of a long option.
            if len(name) >= len("--no-veri") and "--no-verify".startswith(name):
                return "--no-verify skips the pre-commit checks."
            if sub == "push" and (len(name) >= len("--force") and "--force-with-lease".startswith(name)
                                  or len(name) >= len("--mi") and "--mirror".startswith(name)):
                return "force-pushing rewrites shared history."
            if sub == "push" and arg.startswith("+") and len(arg) > 1:
                return "force-pushing rewrites shared history."
            if sub not in SHORT_VALUE or not re.fullmatch(r"-[a-zA-Z]+", arg):
                continue
            for index, flag in enumerate(arg[1:], start=1):
                if flag in SHORT_VALUE[sub]:
                    # A value flag ending the cluster takes the next word as its value.
                    value_next = index == len(arg) - 1
                    break
                if sub == "commit" and flag == "n":
                    return "-n (--no-verify) skips the pre-commit checks."
                if sub == "push" and flag == "f":
                    return "force-pushing rewrites shared history."
    return None


def refuses(check, command):
    """Runs one check; a command nested so deep that the check cannot finish is refused."""
    try:
        return check(command)
    except RecursionError:
        return True


def bounded_pipeline(command):
    words = tokens_of(command)
    if "|" not in words or any(w != "|" and set(w) <= SEPARATOR_CHARS | REDIRECT_CHARS for w in words):
        return False
    last = words[len(words) - 1 - words[::-1].index("|") + 1:]
    if last and last[0] == "wc" and (len(last) == 1 or len(last) == 2 and last[1] in {"-l", "-c", "-w", "-m"}):
        return True
    if not last or last[0] not in {"head", "tail"}:
        return False
    if len(last) == 1:
        return True
    if len(last) != 3 or last[1] not in {"-n", "-c"} or not re.fullmatch(r"[0-9]{1,6}", last[2]):
        return False
    return 0 < int(last[2]) <= (MAX_INTAKE_LINES if last[1] == "-n" else MAX_INTAKE_BYTES)


def intake_dump(command, base, changed_directory=False):
    if bounded_pipeline(command):
        return False
    for words in simple_commands(command):
        words = program(words)
        if not words:
            continue
        name = PurePosixPath(words[0]).name
        if name == "cd":
            changed_directory = True
        if name == "<script>":
            if intake_dump(words[1], base, changed_directory):
                return True
            continue
        if name == "find" and {"-exec", "-execdir"} & set(words) and {"cat", "less", "more"} & {PurePosixPath(w).name for w in words}:
            return True
        if name not in {"cat", "less", "more"}:
            continue
        if changed_directory:
            return True
        paths = [w for w in words[1:] if not w.startswith("-")]
        if not paths:
            # Small literal heredocs construct prompt/body text; unknown stdin is not sized.
            if HEREDOC.search(command) and len(command.encode()) <= MAX_INTAKE_BYTES and len(command.splitlines()) <= MAX_INTAKE_LINES:
                continue
            return True
        total, lines = 0, 0
        for raw in paths:
            path = Path(raw)
            path = path if path.is_absolute() else base / path
            if not path.exists():
                if any(char in raw for char in "$*?["):
                    return True
                continue
            if not path.is_file():
                return True
            if total + path.stat().st_size > MAX_INTAKE_BYTES:
                return True
            with path.open("rb") as stream:
                data = stream.read(MAX_INTAKE_BYTES - total + 1)
            total += len(data)
            if total > MAX_INTAKE_BYTES:
                return True
            lines += data.count(b"\n") + bool(data and not data.endswith(b"\n"))
            if lines > MAX_INTAKE_LINES:
                return True
    return False


try:
    event = json.load(sys.stdin)
    command = event.get("tool_input", {}).get("command", "")
    if not isinstance(command, str):
        raise TypeError("command is not a string")
except Exception:
    deny("the hook input could not be read; refusing rather than guessing.")
TOKEN_SPLIT = r"[\s'\"=;&|<>()`]+"
QUOTED_GLOB = str.maketrans("*?[", "\x01\x02\x03")
# Programs that never hand an argument to a shell, so a quoted pattern given to them stays a pattern.
QUOTE_SAFE = {"grep", "egrep", "fgrep", "rg", "jq", "head", "tail", "wc", "uniq", "cut", "tr", "ls", "cat", "echo"}


def quotes_inert(command):
    """Whether the shell keeps quoted text literal: no substitution, escape, comment, ANSI-C quote or
    here-string can reopen a quote, and every program is a known reader that runs no shell (an
    unknown one, like env, watch or awk's system(), might; rg runs one with --pre)."""
    if re.search(r"\$[({']|`|\\|#|<<|[<>]\(|--pre", command):
        return False
    for words in simple_commands(command):
        run = program(words)
        if not run or PurePosixPath(run[0]).name not in QUOTE_SAFE:
            return False
    return True
tokens = [t for t in re.split(TOKEN_SPLIT, command) if t]
workdir = event.get("tool_input", {}).get("workdir", event.get("tool_input", {}).get("cwd", event.get("cwd", ".")))
try:
    # Quotes join a shell word (sub/'.e'*), so they are dropped rather than split on.
    shell_text = re.sub(r"['\"]", "", without_inert_heredocs(command))
    shell_tokens = [t for t in re.split(r"[\s=;&|<>()`]+", shell_text) if t]
    # The same words with quoted glob characters made inert, only where quotes surely stay quotes.
    inert = without_inert_heredocs(command)
    if quotes_inert(command):
        inert = re.sub(r"'[^']*'|\"[^\"]*\"", lambda m: m.group(0).translate(QUOTED_GLOB), inert)
    marked = [t for t in re.split(r"[\s=;&|<>()`]+", re.sub(r"['\"]", "", inert)) if t]
    unquoted_globs = [any(char in t for char in "*?[") for t in marked]
    secrets = mentioned_secrets(tokens, shell_tokens, directories(command, workdir if isinstance(workdir, str) else "."),
                                unquoted_globs)
except (OSError, ValueError, RecursionError):
    deny("the files a glob names could not be verified; name the files explicitly.")

if os.environ.get("AEION_LOOP_READ_ONLY") == "1":
    fixed = {"git log -5 --oneline", "git diff --stat", "git diff --check", "git status --short",
             "tools/knowledge/knowledge-check", "tools/knowledge/doc-links", "tools/repo-health/repo-health"}
    try:
        words = shlex.split(command)
    except ValueError:
        deny("the read-only loop command could not be parsed.")
    forge = (len(words) >= 3 and words[0] == "gh" and ((words[1] == "issue" and words[2] in {"list", "view", "create", "comment"})
             or (words[1] == "pr" and words[2] in {"list", "view", "checks", "diff", "comment"})
             or words[1:3] == ["run", "list"]))
    doc_for = (len(words) == 3 and words[:2] == ["tools/knowledge/doc-links", "--for"]
               and re.fullmatch(r"[\w.-]+(/[\w.-]+)*", words[2]) and ".." not in words[2].split("/"))
    production = os.environ.get("AEION_PROD_READ_COMMAND")
    if command.strip() not in fixed and not (forge or doc_for or production and command.strip() == production):
        deny("this loop permits fixed read-only checks and finding/review comments only.")
    if any(char in command for char in ";|&<>`$\n"):
        deny(f"read-only loops do not accept shell composition; write finding text to {LOOP_BODIES}<name>.md.")
    # A body file is published: only the loop's own scratch files, never an arbitrary local file.
    if forge:
        workdir = Path(event["tool_input"].get("workdir", event["tool_input"].get("cwd", event.get("cwd", "."))))
        for i, word in enumerate(words):
            if word == "--recover" or word.startswith("--recover="):
                deny("read-only loops do not recover input from local files.")
            if re.fullmatch(r"-[^-]*F.*", word) and word != "-F":
                deny(f"read-only loops pass a body file as a separate word: -F {LOOP_BODIES}<name>.md.")
            if word in ("-F", "--body-file") or word.startswith("--body-file="):
                body = word.split("=", 1)[1] if "=" in word else (words[i + 1] if i + 1 < len(words) else "")
                if not re.fullmatch(re.escape(LOOP_BODIES) + r"[\w.-]+", body) or ".." in body \
                        or (workdir / body).is_symlink() or (workdir / LOOP_BODIES).is_symlink():
                    deny(f"read-only loops publish only body files under {LOOP_BODIES}.")

# Secret files: reading one is refused; any other mention is a human's call.
if secrets:
    if READERS & set(tokens):
        deny(f"it reads a secret file ({', '.join(secrets)}). Secrets are never read or printed "
             "(to search for the name itself, use the Grep tool).")
    ask(f"The command mentions a secret file ({', '.join(secrets)}).")

# Environment dumps hold keys.
if "printenv" in tokens or refuses(env_dump, command):
    deny("it prints an environment, which holds keys (to search for a name, use the Grep tool; for prose, write it to a file).")
if refuses(docker_inspect_dump, command):
    deny("docker inspect without a narrow --format shows the container's environment.")
if refuses(compose_config, command):
    deny("docker compose config prints the configuration with the secrets filled in.")

# History and checks are not bypassed.
if re.search(r"\bgit\s+push\b", command) and re.search(r"\s(-f|--force|--force-with-lease)(\s|=|$)", command):
    deny("force-pushing rewrites shared history.")
if re.search(r"\bgit\b", command) and "--no-verify" in tokens:
    deny("--no-verify skips the pre-commit checks.")
bypass = refuses(git_bypass, command)
if bypass:
    deny(bypass if isinstance(bypass, str) else "the git command is nested too deeply to verify.")
try:
    base = event["tool_input"].get("workdir", event["tool_input"].get("cwd", event.get("cwd", ".")))
    if intake_dump(command, Path(base)):
        deny(INTAKE_REASON)
except (OSError, TypeError, RecursionError):
    deny("the dump size could not be verified; " + INTAKE_REASON)
sys.exit(0)
