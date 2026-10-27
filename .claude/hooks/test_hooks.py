#!/usr/bin/env python3
"""Tests for the hooks in this folder: each gets a sample event on stdin.

Run with: python3 .claude/hooks/test_hooks.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
ROOT = HOOKS.parents[1]
RUN = str(abs(hash(tempfile.mkdtemp())))
failures, passes = [], 0


def run_hook(name, tool_input, cwd=ROOT, **extra):
    event = json.dumps({"tool_input": tool_input, **extra})
    return subprocess.run([sys.executable, str(cwd / ".claude/hooks" / name)], input=event,
                          capture_output=True, text=True, cwd=cwd)


def expect(label, result, code, stdout_has=None, stderr_has=None):
    global passes
    if (result.returncode == code and (stdout_has is None or stdout_has in result.stdout)
            and (stderr_has is None or stderr_has in result.stderr)):
        passes += 1
    else:
        failures.append(f"{label}: exit {result.returncode}, stdout {result.stdout!r}, stderr {result.stderr!r}")


# guard-bash: refused, asked, allowed.
for command in ["cat .env", "cat env.local", "printenv", "cat /proc/1/environ", "python3 -c 'import os; print(os.environ)'", "node -e 'console.log(process.env)'",
                "python3 <<'EOF'\nimport os\nprint(os.environ)\nEOF", "echo 'print(dict(os.environ))' | python3",
                "python3 -c 'from os import environ; print(environ)'", "cd /proc/self && cat environ",
                "npx tsx -e 'console.log(process.env)'", "ruby -e 'p ENV.to_h'", "docker exec cyclone-brain-1 env",
                "sudo env", "env -0", "/usr/bin/env", "export", "declare -x",
                "docker exec -u root cyclone-brain-1 env", "sudo -u root env", "env > /tmp/x", "  env",
                "sh -c env", "(env)", "time env", "ssh vps 'env'", "awk 'BEGIN{for(k in ENVIRON) print k}'",
                "python3 -c 'import os; print(os.environb)'", "jq -n env",
                "env\necho done", "bash <<X\nenv\nX", "cd /tmp\nset\nls", "env 2>&1", "env 1>f",
                "env -u HOME | sort", "env --", "env FOO=1 > out.txt", "xargs env </dev/null", "declare",
                "typeset -x", "ps eww", "ps auxe", "docker exec c sh -c declare", "su -c env",
                "(env)|sort", "echo hi;(env)", "true&&(env)", "ssh vps 'cd /app\ndocker exec cyclone-brain-1 env'",
                "bash -c 'cd /tmp\nenv'", "bash -lc env", "sh -xc env", "bash -c -- env",
                "docker compose exec brain env", "docker container exec c env", "xargs -n 1 env",
                "xargs -I {} env", "ssh vps -- env", "ps -E", "ps -wwE", "docker compose run --rm -v a:b brain env",
                "docker compose -f compose.yml exec brain env", "docker compose --project-directory /x exec brain env",
                "docker --context x exec c env", "for c in a b; do docker exec $c env; done",
                "while read c; do docker exec $c env; done < f", "if true; then env; fi", "{ env; }",
                "docker compose -f x config", "kubectl exec pod -- env",
                "ssh host 'cd /app && docker compose config'", "bash -c 'docker compose config'",
                "ssh -o ConnectTimeout=10 host \\\n'docker exec c env | grep KEY'", "docker compose exec \\\nbrain env",
                "ssh host -t 'docker exec c env'", "docker inspect --format '{{json .}}' c",
                "docker inspect $(docker ps -q -f name=brain)", "cd /app && docker compose -f compose.yml ps && docker inspect c",
                "docker --context x inspect c", "docker inspect -f '{{json .Config}}' c", "docker inspect --format='{{.Config.Env}}' c",
                "cat <<'EOF' | ssh host bash\nenv\nEOF", "ssh h " * 1200 + "env",
                "docker inspect --format json c", "docker inspect -f json c", "docker inspect --format=json c",
                "docker inspect --format '' c", "docker inspect -f '{{. | json}}' c",
                "docker inspect $(docker ps -q\n)", "docker inspect $(docker ps -q;)", "docker inspect -f '{{- json . -}}' c", "docker inspect web",
                "docker compose config", "git push --force origin main", "git commit --no-verify -m x",
                "git commit -n -m x", "git commit -anm x", "git push origin +HEAD:main", "git push -fu origin main",
                "git -c core.hooksPath=/dev/null commit -m x", "bash -c 'git commit -n -m x'",
                "git commit --no-verif -m x", "git merge --no-veri topic", "git --config-env=core.hooksPath=PWD commit -m x",
                "GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=/dev/null git commit -m x",
                "git config core.hooksPath /dev/null", "git push --force-with origin main", "git push --force-with-lease=main origin main",
                "git config --unset core.hooksPath", "git config --local core.hooksPath .git/hooks", "export GIT_CONFIG_KEY_0=core.hooksPath",
                "git --config-env core.hooksPath=PWD commit -m x", "git push --mirror origin"]:
    expect(f"bash deny: {command}", run_hook("guard-bash.py", {"command": command}), 2)
expect("bash ask: mentions a secret", run_hook("guard-bash.py", {"command": "ls -la .env"}), 0, '"ask"')
for command in ["git status --short", "git commit -m 'the environment check'",
                "grep -rn environment knowledge", "/usr/bin/env python3 tools/x.py", "npm config set registry x", "git commit -m 'block env'", "ps -ef", "ps aux",
                "ps -o etime -p 1", "declare -a arr", "export FOO=bar", "python3 - <<'EOF'\nprint(env)\nEOF",
                "gh pr create --body 'dumps (env)'", "ps -eo pid,etime,args", "ps -C node", "ps axo pid,etime",
                "docker compose logs brain | grep -i config", "docker compose config -q", "ssh host python3 - <<'EOF'\nprint(sorted(set([1])))\nEOF",
                "docker compose config --services", "command -v env", "docker inspect -f '{{.Config.Image}}' c",
                "docker inspect -f '{{.Config.Entrypoint}}' c", "docker inspect -f '{{.State.Health.Status}}' c", "docker inspect $(docker ps -q) --format '{{.Name}} {{.State.Status}}'",
                "echo $(date) && git status", "echo $(date;) && git status", "gh pr create --body \"$(cat <<'EOF'\ndumps (env)\nEOF\n)\"", "cat env.example.local", "npm test", "set -euo pipefail",
                "git commit -m 'use head -n 5'", "git commit -am wip", "git commit -mnew", "git push -u origin task/x",
                "git push -n origin main", "git -C repo status", "git commit -m -n", "git commit -am -n",
                "git push --follow-tags origin task/x", "git log --no-verbose",
                "git config core.hooksPath tools/git-hooks", "git config --get core.hooksPath",
                "grep -rn core.hooksPath README.md", "git commit -m 'document core.hooksPath setup'"]:
    result = run_hook("guard-bash.py", {"command": command})
    expect(f"bash allow: {command}", result, 0)
    if '"ask"' in result.stdout:
        failures.append(f"bash allow asked instead: {command}")

# Read-only loops publish only their own body files, never an arbitrary local file.
def run_read_only(command, cwd):
    event = json.dumps({"tool_input": {"command": command}, "cwd": str(cwd)})
    return subprocess.run([sys.executable, str(HOOKS / "guard-bash.py")], input=event, capture_output=True,
                          text=True, cwd=ROOT, env={"PATH": "/usr/bin:/bin", "AEION_LOOP_READ_ONLY": "1"})


with tempfile.TemporaryDirectory() as loop_dir:
    loop = Path(loop_dir)
    (loop / ".aeion/loop-bodies").mkdir(parents=True)
    (loop / ".aeion/loop-bodies/finding.md").write_text("Finding\n")
    (loop / ".aeion/loop-bodies/link.md").symlink_to(loop / "outside.md")
    for command in ["gh issue create --title x --body-file .aeion/loop-bodies/finding.md --label loop:outer",
                    "gh pr comment 7 -F .aeion/loop-bodies/finding.md", "gh pr diff 7",
                    "tools/knowledge/doc-links --for tools/repo-health/repo-health"]:
        expect(f"read-only allow: {command}", run_read_only(command, loop), 0)
    for command in ["gh issue create --title x --body-file /home/u/.config/gh/hosts.yml",
                    "gh issue comment 3 -F ../.aeion/loop-bodies/finding.md",
                    "gh pr comment 7 --body-file=.aeion/loop-bodies/../../secret.md",
                    "gh pr comment 7 -F .aeion/loop-bodies/link.md", "gh issue create --recover state.json",
                    "gh issue create --title x --body 'a\nb'", "git diff origin/main...HEAD",
                    "tools/knowledge/doc-links --for ../outside", "tools/knowledge/doc-links --diff origin/main",
                    "gh issue comment 1 -F/etc/hostname", "gh issue comment 1 -F=/etc/hostname",
                    "gh pr comment 7 -wF/etc/hostname"]:
        expect(f"read-only deny: {command}", run_read_only(command, loop), 2)

# guard-path: secrets refused, templates allowed.
for path in ["/repo/.env", "/repo/env.local", "/x/server.pem", "/h/auth.json", "/h/.netrc", "/h/.ssh/id_ecdsa",
             "/x/client.p12", "/repo/.envrc", "/h/.npmrc"]:
    expect(f"path deny: {path}", run_hook("guard-path.py", {"file_path": path}), 2)
expect("path deny: NotebookEdit names its file notebook_path",
       run_hook("guard-path.py", {"notebook_path": "/repo/.env"}, tool_name="NotebookEdit"), 2)
expect("sign-off ignores a session id that is a path", run_hook("sign-off.py", {}, session_id="../../etc/x"), 0)
expect("sign-off ignores unreadable input", subprocess.run([sys.executable, str(HOOKS / "sign-off.py")], input="{",
                                                           capture_output=True, text=True), 0)

# A glob is judged by the files it expands to, as the shell would expand it.
glob_dir = Path(tempfile.mkdtemp())
(glob_dir / ".env").write_text("KEY=x\n")
(glob_dir / "notes.md").write_text("x\n")
for command in ["head .env*", "grep -r . .e*", "base64 .en?", "tail .[e]nv", f"head {glob_dir}/.e*"]:
    expect(f"bash deny glob: {command}", run_hook("guard-bash.py", {"command": command, "workdir": str(glob_dir)}), 2)
expect("bash ask: a glob that names a secret", run_hook("guard-bash.py", {"command": "ls .e*", "workdir": str(glob_dir)}), 0, '"ask"')
for command in ["ls *", "head *.md", "grep -r x .", "wc -l .x*"]:
    expect(f"bash allow glob: {command}", run_hook("guard-bash.py", {"command": command, "workdir": str(glob_dir)}), 0)
expect("bash deny names the Grep tool for searches", run_hook("guard-bash.py", {"command": "grep -rn id_rsa tools"}), 2,
       stderr_has="Grep tool")
shutil.rmtree(glob_dir)
for path in ["/repo/.env.example", "/repo/env.example.local", str(ROOT / "AGENTS.md")]:
    expect(f"path allow: {path}", run_hook("guard-path.py", {"file_path": path}), 0)

# Unreadable policy input is an explicit denial, never a traceback or an implicit allow.
for raw in ["{", "null", "[]", "{}", '{"tool_input": []}', '{"tool_input": {"path": 123}}',
            '{"tool_input": {"file_path": null}}', '{"tool_input": {"file_path": ""}}']:
    result = subprocess.run([sys.executable, str(HOOKS / "guard-path.py")], input=raw,
                            capture_output=True, text=True, cwd=ROOT)
    expect(f"path deny malformed: {raw}", result, 2)
    if "Traceback" in result.stderr:
        failures.append("guard-path exposed a traceback instead of a denial")
expect("path allow: Grep can use its implicit root", run_hook("guard-path.py", {"pattern": "fixture"}, tool_name="Grep"), 0)
expect("path allow: Grep can use an empty default path", run_hook("guard-path.py", {"path": "", "pattern": "fixture"}, tool_name="Grep"), 0)

# Intake decisions use public fixtures; no submitted command is executed.
with tempfile.TemporaryDirectory() as intake_dir:
    intake = Path(intake_dir)
    small, many, wide = [intake / name for name in ("small.txt", "many.log", "wide.txt")]
    small.write_text("answer\n")
    many.write_text("line\n" * 401)
    wide.write_text("x" * 65537)
    for path in (many, wide):
        expect("intake denies full Read", run_hook("guard-path.py", {"file_path": str(path)}, tool_name="Read"), 2, stderr_has="bounded-intake.md")
        for name in ("cat", "less", "more"):
            expect("intake denies file dump", run_hook("guard-bash.py", {"command": f"{name} '{path}'"}), 2, stderr_has="bounded-intake.md")
        for name in ("Edit", "Write"):
            expect("intake keeps large edits available", run_hook("guard-path.py", {"file_path": str(path)}, tool_name=name), 0)
    expect("intake allows small Read", run_hook("guard-path.py", {"file_path": str(small)}, tool_name="Read"), 0)
    expect("intake allows bounded Read window", run_hook("guard-path.py", {"file_path": str(many), "offset": 350, "limit": 20}, tool_name="Read"), 0)
    expect("intake refuses long line despite line limit", run_hook("guard-path.py", {"file_path": str(wide), "limit": 1}, tool_name="Read"), 2)
    for limit in (0, -1, 401, True):
        expect("intake rejects ineffective large Read limit", run_hook("guard-path.py", {"file_path": str(many), "limit": limit}, tool_name="Read"), 2)
    expect("intake treats Read offset 0 as the start", run_hook("guard-path.py", {"file_path": str(many), "offset": 0, "limit": 20}, tool_name="Read"), 0)
    for target in ({"path": intake_dir}, {}):
        expect("intake denies unlimited content Grep", run_hook("guard-path.py", {**target, "pattern": ".", "output_mode": "content", "head_limit": 0}, tool_name="Grep"), 2, stderr_has="bounded-intake.md")
        expect("intake keeps unlimited file-name Grep", run_hook("guard-path.py", {**target, "pattern": ".", "output_mode": "files_with_matches", "head_limit": 0}, tool_name="Grep"), 0)
    expect("intake denies unbounded large-file Grep", run_hook("guard-path.py", {"path": str(many), "pattern": ".", "output_mode": "content"}, tool_name="Grep"), 2)
    for fields in ({"head_limit": 80}, {"limit": 80}, {"output_mode": "count"}, {"output_mode": "files_with_matches"}):
        expect("intake keeps targeted Grep", run_hook("guard-path.py", {"path": str(many), "pattern": "line", **fields}, tool_name="Grep"), 0)
    for suffix in ("head -n 80", "head -c 65536", "tail -n 80", "wc -l"):
        expect("intake allows terminal limiter", run_hook("guard-bash.py", {"command": f"cat '{many}' | {suffix}"}), 0)
    for command in (f"head -n 80 '{small}'; cat '{many}'", f"cat '{many}'; head -n 80 '{small}'",
                    f"cat '{many}' | tail -n +1", f"cat '{many}' | head -n 999999", f"cat '{many}' | echo head",
                    f"cat '{many}' 1>&2 | head -n 80", f"cat < '{many}'", "find . -type f -exec cat {} \\;",
                    "cat *.log", "cat $LOG_FILE"):
        expect("intake rejects an ineffective limiter", run_hook("guard-bash.py", {"command": command}), 2, stderr_has="bounded-intake.md")
    expect("intake allows small cat", run_hook("guard-bash.py", {"command": f"cat '{small}'"}), 0)
    boundary = intake / "boundary.txt"
    for data in ("line\n" * 400, "x" * 65536):
        boundary.write_text(data)
        expect("intake allows exact threshold Read", run_hook("guard-path.py", {"path": str(boundary)}, tool_name="Read"), 0)
        expect("intake allows exact threshold cat", run_hook("guard-bash.py", {"command": f"cat '{boundary}'"}), 0)
    expect("intake respects native Bash workdir", run_hook("guard-bash.py", {"command": "cat many.log", "workdir": intake_dir}), 2)
    expect("intake refuses unknown cwd after cd", run_hook("guard-bash.py", {"command": f"cd '{intake}'; cat many.log"}), 2)
    expect("intake keeps secret refusal ahead of limiter", run_hook("guard-bash.py", {"command": "cat .env | head -n 80"}), 2, stderr_has="secret")
    for count in ("²", "9" * 1000):
        expect("intake refuses malformed limiter count", run_hook("guard-bash.py", {"command": f"cat '{many}' | head -n {count}"}), 2, stderr_has="bounded-intake.md")
    far = intake / "distant.log";far.write_text("z\n" * 550000)
    expect("intake bounds distant window scanning", run_hook("guard-path.py", {"path": str(far), "offset": 550000, "limit": 1}, tool_name="Read"), 2)
    small.write_text("x" * 35000);boundary.write_text("y" * 35000)
    expect("intake bounds combined cat operands", run_hook("guard-bash.py", {"command": f"cat '{small}' '{boundary}'"}), 2)
    expect("intake keeps cwd uncertainty in nested shells", run_hook("guard-bash.py", {"command": f"cd '{intake}' && sh -c 'cat many.log'"}), 2)
    expect("intake allows a bounded nested shell after cd", run_hook("guard-bash.py", {"command": f"cd '{intake}' && sh -c 'cat many.log | head -n 80'"}), 0)
    wide.write_text("x" * 65537 + "\nanswer\n")
    expect("intake skips a long line within scan budget", run_hook("guard-path.py", {"path": str(wide), "offset": 2, "limit": 1}, tool_name="Read"), 0)

# Run after-edit against real child processes with controlled outcomes.
after = Path(tempfile.mkdtemp())
for folder in (".claude/hooks", "tools/knowledge", "knowledge"):
    (after / folder).mkdir(parents=True, exist_ok=True)
shutil.copy(HOOKS / "after-edit.py", after / ".claude/hooks/after-edit.py")
document = after / "knowledge/fixture.md"
document.write_text("Synthetic document.\n")
checker = after / "tools/knowledge/knowledge-check"


def fake_check(path, body):
    path.write_text("#!/usr/bin/env python3\n" + body)
    path.chmod(0o755)


after_session = f"after-edit-{RUN}"
for label, body, code, diagnostic in [
    ("success", "raise SystemExit(0)\n", 0, ""),
    ("stderr failure", "import sys\nprint('synthetic failure', file=sys.stderr)\nraise SystemExit(1)\n", 2, "synthetic failure"),
    ("timeout", "import time\ntime.sleep(3)\n", 2, "timed out"),
]:
    fake_check(checker, body)
    result = run_hook("after-edit.py", {"file_path": str(document)}, cwd=after, session_id=after_session)
    expect(f"after-edit: {label}", result, code)
    if diagnostic and diagnostic not in result.stderr:
        failures.append(f"after-edit {label}: missing diagnostic")
    if len(result.stderr.splitlines()) > 15:
        failures.append(f"after-edit {label}: diagnostic exceeds 15 lines")
fake_check(checker, "import sys\nprint('synthetic failure', file=sys.stderr)\nraise SystemExit(1)\n")
expect("after-edit: NotebookEdit's notebook_path is checked", run_hook("after-edit.py", {"notebook_path": str(document)},
       cwd=after, session_id=after_session), 2, stderr_has="synthetic failure")
heartbeat = after / "heartbeat"
child = (f"from pathlib import Path\nimport time\npath = Path({str(heartbeat)!r})\n"
         "for number in range(200):\n    path.write_text(str(number))\n    time.sleep(0.05)\n")
fake_check(checker, "import subprocess, sys, time\n"
           f"subprocess.Popen([sys.executable, '-c', {child!r}])\n"
           "time.sleep(10)\n")
started = time.monotonic()
expect("after-edit: a timed-out checker terminates its descendants", run_hook("after-edit.py",
       {"file_path": str(document)}, cwd=after, session_id=after_session), 2)
if time.monotonic() - started > 5:
    failures.append("after-edit waited for a descendant after its checker timed out")
last_heartbeat = heartbeat.read_text() if heartbeat.exists() else None
time.sleep(0.2)
if heartbeat.exists() and heartbeat.read_text() != last_heartbeat:
    failures.append("after-edit left a descendant running after the timeout")
checker.unlink()
expect("after-edit: missing checker fails", run_hook("after-edit.py", {"file_path": str(document)},
       cwd=after, session_id=after_session), 2)

source = after / "source.py"
source.write_text("value = 1\n")
linker = after / "tools/knowledge/doc-links"
fake_check(linker, "import sys\nprint('synthetic link failure', file=sys.stderr)\nraise SystemExit(1)\n")
expect("after-edit: failed doc hint is visible", run_hook("after-edit.py", {"file_path": str(source)},
       cwd=after, session_id=after_session), 2)
fake_check(linker, "print('')\n")
uncovered = run_hook("after-edit.py", {"file_path": str(source)}, cwd=after, session_id=after_session)
expect("after-edit: an uncovered file gets no hint", uncovered, 0)
if uncovered.stdout.strip():
    failures.append("after-edit hinted an empty covering doc")
fake_check(linker, "print('knowledge/a doc.md')\n")
hint = run_hook("after-edit.py", {"file_path": str(source)}, cwd=after, session_id=after_session)
expect("after-edit: a spaced doc is one hint", hint, 0, "covered by knowledge/a doc.md")
for prefix in ("claude-edited-", "claude-doc-hint-"):
    (Path(tempfile.gettempdir()) / f"{prefix}{after_session}").unlink(missing_ok=True)
shutil.rmtree(after)

# sign-off: in a throwaway repo, a code change without its doc blocks once, then passes.
tmp = Path(tempfile.mkdtemp())
for rel in (".claude/hooks/sign-off.py", ".claude/hooks/secret_names.py", "tools/knowledge/doc-links"):
    (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(ROOT / rel, tmp / rel)
(tmp / "knowledge/components").mkdir(parents=True)
(tmp / "work").mkdir()
(tmp / "src").mkdir()
(tmp / "knowledge/components/x.md").write_text("---\ntype: Component\nsources:\n  - id: c\n    resource: ../../src/a.ts\n---\n")
(tmp / "src/a.ts").write_text("export const a = 1;\n")
(tmp / "work/current.md").write_text("# Current work\n")
git = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid"]
for args in (["init", "-q", "-b", "main"], ["add", "."], ["commit", "-qm", "base"], ["switch", "-qc", "task/x"]):
    subprocess.run(git + args, cwd=tmp, capture_output=True)
(tmp / "src/a.ts").write_text("export const a = 2;\n")


def stop(session, active=False):
    return subprocess.run([sys.executable, str(tmp / ".claude/hooks/sign-off.py")], cwd=tmp, capture_output=True,
                          text=True, input=json.dumps({"session_id": f"{session}-{RUN}", "stop_hook_active": active}))


expect("sign-off: a session that edited nothing passes", stop("idle"), 0)
if '"block"' in stop("idle").stdout:
    failures.append("sign-off blocked a session that edited nothing")
with (Path(tempfile.gettempdir()) / f"claude-edited-busy-{RUN}").open("a") as f:
    f.write("src/a.ts\n")
first = stop("busy")
expect("sign-off: code without its doc blocks", first, 0, '"decision": "block"')
expect("sign-off: names the doc", first, 0, "knowledge/components/x.md")
if '"block"' in stop("busy").stdout:
    failures.append("sign-off blocked twice on the same findings")

# A filename with spaces and accents must survive both Git and the edited-file log.
special = "src/café file.py"
(tmp / special).write_text("# Spec: knowledge/components/x.md\nvalue = 1\n")
subprocess.run(git + ["add", special], cwd=tmp, capture_output=True, check=True)
subprocess.run(git + ["commit", "-qm", "special path"], cwd=tmp, capture_output=True, check=True)
(tmp / special).write_text("# Spec: knowledge/components/x.md\nvalue = 2\n")
with (Path(tempfile.gettempdir()) / f"claude-edited-special-{RUN}").open("a") as f:
    f.write(special + "\n")
special_result = stop("special")
expect("sign-off: a spaced accented path is checked", special_result, 0, '"decision": "block"')
if special not in json.loads(special_result.stdout or "{}").get("reason", ""):
    failures.append("sign-off lost a spaced accented path")

# Local mode (git config aeion.mode local) skips the sign-off reminder for the same change.
for session in ("team", "local"):
    with (Path(tempfile.gettempdir()) / f"claude-edited-{session}-{RUN}").open("a") as f:
        f.write("src/a.ts\n")
expect("sign-off: a fresh team session blocks", stop("team"), 0, '"decision": "block"')
subprocess.run(git + ["config", "aeion.mode", "local"], cwd=tmp, capture_output=True, check=True)
local_result = stop("local")
expect("sign-off: local mode passes", local_result, 0)
if '"block"' in local_result.stdout:
    failures.append("sign-off blocked in local mode")

# session-start: at most 25 lines, and it names the flow mode.
def session_start(mode):
    # Environment configuration outranks a developer's own repository setting.
    env = {**os.environ, "GIT_CONFIG_COUNT": "1", "GIT_CONFIG_KEY_0": "aeion.mode", "GIT_CONFIG_VALUE_0": mode}
    return subprocess.run([sys.executable, str(HOOKS / "session-start.py")], capture_output=True, text=True, cwd=ROOT, env=env)


result = session_start("team")
expect("session-start runs", result, 0, "git status")
expect("session-start names the team flow", result, 0, "Æion Factory mode: team")
if len(result.stdout.strip().split("\n")) > 25:
    failures.append("session-start printed more than 25 lines")
expect("session-start names local mode", session_start("local"), 0, "Æion Factory mode: local")

print(f"hook tests: {passes} passed, {len(failures)} failed")
for f in failures:
    print(f"  FAIL {f}")
sys.exit(1 if failures else 0)
