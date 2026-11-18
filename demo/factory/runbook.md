# Factory local VPS runbook (S4)

This runbook covers running the Æion Feature Cockpit and Agora factory controller on a small host or local VPS with fake inference. Nothing here authorizes paid inference, remote merges, or production deployment without explicit gates. The default worker simulates builds; the pinned target profile runs the real Quarkus forum and Gradle checks locally without calling a model.

The backup and restore drill below validates only the factory SQLite state store (`demo/.local/factory/factory.db`). Restoring the separate product PostgreSQL database requires its own schema procedure.

## 1. What runs

One Python server on loopback exposes both interfaces and API routes:

| Surface | Path | Purpose |
| --- | --- | --- |
| Feature cockpit | `/` | Paginated feature catalog, build status, budget caps, and events (alias: `/factory`) |
| Model lab | `/lab` | Sandbox task runner, paginated run history, model comparison, checkpoints, and stack health |

The controller writes an owner-only SQLite WAL database and temporary worktrees inside `demo/.local/`, which stays ignored by Git and outside product outputs.

## 2. Prerequisites

- Python 3.13+ (`demo/.local/venv` runs Python 3.15 here) and `git` on `PATH`.
- Fake inference requires no API provider. GitHub publishing stays dry-run unless `--for-real` is passed with `GH_API_KEY` set; tokens are read at request time and never logged.
- A dedicated unprivileged user owns the checkout and `demo/.local/`.

## 3. Pi extension requirement

Start Pi agents with the template extension loaded so skills and hooks initialize properly:

```bash
pi -e .pi/extensions/template/index.js
```

`flue run` (2.3.1) accepts no `-e` flag itself, so keep `.pi/extensions/template/index.js` present inside every prepared agent workspace before launching Flue.

## 4. Trust boundary

Review [`trust-model.md`](trust-model.md) before enabling any new capability. Model outputs are treated strictly as untrusted data: generated code runs inside OpenShell, diffs undergo strict path validation, protected checks and deterministic rules run outside agent reach, and the publisher refuses unreviewed artifacts. Nothing merges without passing required checks and two independent reviews.

## 5. Configuration allowlist

| Variable | Default | Meaning |
| --- | --- | --- |
| `AEION_COCKPIT_PORT` | `8088` | Loopback listen port |
| `AEION_LOCAL_DIR` | `demo/.local` | Owner-only state directory (`0700`) |
| `AEION_DATA_DIR` | `demo/.local/data` | Cockpit and lab metrics store |
| `AEION_WORK_DIR` | `demo/.local/work` | Disposable sandbox workspaces |
| `AEION_DAILY_LIMIT_USD`, `AEION_AUTHOR_MAX_USD`, `AEION_REVIEW_MAX_USD` | From `demo/budget.conf` (`150`, `50`, `1`) | Hard spending ceilings (`$150/day`, `$50/execution`, `$1/vote`) |

Never pass secrets on the command line or inside service unit files. First startup generates `demo/.local/factory/admin.token` (`0600`), rotating the bootstrap token on every login.

### 5.1 Credentials: one key per role

Copy the committed root [`.env.example`](../../.env.example) locally and issue three separate GitHub fine-grained tokens scoped solely to `OualidGuennif/aeion-autonomous-forum` with explicit expiration dates:

| Key | Role | Fine-grained permissions | Process owner |
| --- | --- | --- | --- |
| `GH_BUILD_KEY` | Build | Contents read-only, Pull requests read-only | Trusted source sync only; never an agent |
| `GH_API_KEY` | Publish | Contents read/write, Pull requests read/write | Isolated publisher for a single PR |
| `GH_RELEASE_KEY` | Release | Contents read/write, Pull requests read/write, Administration read-only | Isolated release process |

`demo/factory/keys.py` enforces role isolation and `demo/app/settings.py` scrubs publish credentials at startup. Missing keys fail closed.

The maintainer bootstrap imports GitHub Actions workflows alongside the product backend and temporarily needs **Workflows read/write** permission on that repository, after which that permission should be removed. If GitHub returns HTTP 403 before creating a branch or PR, re-arm the permission and run `bootstrap.py resume-publication --state <bootstrap-state>` in the publisher environment rather than repeating model reviews or forcing a new author attempt.

### 5.2 Branch protection and required status checks

Both `main` and `develop` require pull requests, linear history, resolved conversations, no force-pushes or branch deletions (admins included), and all five CI checks: `Knowledge, links and repository health`, `Product artifacts`, `secret-scan`, `dependency-scan`, and `sast-scan`. `main` also enforces up-to-date branches before merge, whereas `develop` allows parallel merges without constant rebasing. `Product artifacts` runs `.github/scripts/check_product.py` independently of factory reviewers.

## 6. Start and stop

Foreground startup from the checkout directory:

```bash
cd /srv/aeion-factory
python3 demo/run.py
```

The launcher re-executes inside `demo/.local/venv/bin/python` automatically (or falls back smoothly if you run `demo/install.py` first). Example `systemd` unit for Linux hosts:

```ini
[Unit]
Description=Aeion cockpit and Agora factory board (local, fake inference)
After=network.target

[Service]
Type=simple
User=aeion
WorkingDirectory=/srv/aeion-factory
Environment=AEION_COCKPIT_PORT=8088
ExecStart=/usr/bin/python3 demo/run.py
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/srv/aeion-factory/demo/.local

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload && sudo systemctl enable --now aeion-factory
curl -fsS http://127.0.0.1:8088/api/health
```

Stop with `sudo systemctl stop aeion-factory`. Because the server binds loopback and validates `Host` and `Origin` headers, any SSH tunnel or reverse proxy must preserve both.

## 7. Health checks

```bash
curl -fsS http://127.0.0.1:8088/api/health
curl -fsS -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8088/factory
```

Unauthenticated requests to `/api/factory/board` return `401`. Read the admin token directly from `demo/.local/factory/admin.token` in your editor and avoid pasting it into logs, tickets, or chat.

## 8. Verified backups

Take live SQLite backups safely during WAL activity and immediately run integrity verification:

```bash
cd /srv/aeion-factory/demo
.local/venv/bin/python -m factory.restore \
  .local/factory/factory.db \
  /var/backups/aeion/factory-$(date -u +%Y%m%dT%H%M%SZ).db
```

The command prints a JSON receipt and exits non-zero if validation fails (`source_missing`, `not_a_database`, `integrity:...`, or `missing_tables:...`). Keep 14 daily backups plus the first backup of each month, and fail cron/timer jobs on any non-zero exit.

## 9. Restore procedure

1. Stop the controller process so no writer remains active.
2. Verify the candidate backup file before touching live state:
   ```bash
   cd /srv/aeion-factory/demo
   .local/venv/bin/python -c \
     "from factory.restore import verify_db; import json; print(json.dumps(verify_db('/var/backups/aeion/factory-XXXX.db')))"
   ```
3. Move `demo/.local/factory/factory.db` (plus any `-wal` and `-shm` files) to `.pre-restore` rather than deleting them.
4. Copy the verified backup into place and enforce `chmod 0600`.
5. Start the controller and check `/api/health`, `/factory`, and build records.
6. Remove `.pre-restore` files only after verifying the restored board.

On startup, `Store` moves any expired leases into `held/reconciliation_needed` and preserves attempt IDs. Always inspect costs and remote forge state before cancelling an interrupted attempt and retrying, since a crash does not prove an external call had no effect.

## 10. Rollback

Keep code and SQLite state decoupled. To roll back a broken release, stop the controller, restore the latest verified database backup, restart the service, verify health endpoints, and check out the previous Git revision once state matches its schema version.

## 11. Common holds and actions

| Symptom | Meaning | Action |
| --- | --- | --- |
| Held `dependency_missing` | A prerequisite feature has not merged yet | Build and merge the prerequisite first |
| Held `qualification_missing` | Frozen contract or sandbox bound missing | Restore qualification before queueing |
| Held `owner_review_required` | Diff touches sensitive paths or rules | Review the diff locally before proceeding |
| Held `reconciliation_needed` | Interrupted attempt or moved base commit | Reconcile remote/budget state before retrying |
| Publisher `uncertain` | Unknown GitHub PR/merge state | Let publisher reconcile; do not re-publish |
| `failed` at `correction.round` 0 or 1 | Refusal or CI failure triggered next round | Wait for the automatic retry or inspect evidence |
| Held `ci_failed` (`correction.exhausted`) | Required CI stayed red across rounds | Read failing check names in evidence, then cancel |
| Held `reviewer_rejected` / `correction_unchanged` | Reviewers rejected diff or retry changed nothing | Read reviewer feedback, cancel, and adjust spec |
| Held `reviewer_rejected` (legacy v1) | Older envelope lacked base diff | Run `python -m factory.review_context BUILD_ID` once from `demo/` |
| Held `reviewer_failed` (`REVIEW_RESULT_MISSING`) | Reviewer timed out or returned untyped reply | Retry failed votes once (`--retry-failed-review`) |

## 12. Limits of this local runbook

- Tier 3 OpenShell sandboxing in local Docker Desktop is dev isolation, not a hostile-code microVM boundary.
- Without `--for-real` and `GH_API_KEY`, no remote GitHub branch, PR, or merge executes.
- Product PostgreSQL migrations, schema backups, live deployments, and external hosting remain separate operations.

## 13. Release API

The controller provides programmatic release endpoints (`GET /api/factory/releases`, `POST /api/factory/release`), while the browser cockpit intentionally omits synthetic canary buttons and shows Staging/Production as `Not deployed yet` until verified deployments exist.

| Action | Payload on `POST /api/factory/release` | Effect |
| --- | --- | --- |
| Stage | `{"action":"stage","features":[...]}` | Creates a staged release record |
| Validate | `{"action":"validate"}` | Moves canary share to 25% |
| Advance | `{"action":"advance"}` | Advances after dwell completes and gate passes |
| Immediate full deploy | `{"action":"deploy_now"}` | Sets 100% (`immediate_full_deploy`) |
| Rollback | `{"action":"rollback","reason":"..."}` | Drops share to 0% (`rolled_back`) |
| Flag | `{"action":"flag","name":"dark_mode","enabled":true}` | Records a release flag change |

`AEION_RELEASE_SCALE` shortens 6 h / 12 h dwell timers during local drills, and `AEION_REDIS_URL` enables Redis instead of the file fallback:

```bash
docker run -d --name aeion-redis -p 6399:6379 redis:7-alpine
AEION_REDIS_URL=redis://127.0.0.1:6399 python3 demo/run.py
```

Worker session tokens issue and revoke via `POST /api/factory/session` (`{"action":"issue","agent_id":"...","build_id":"..."}`); tokens appear once, with only digests and audit events stored locally (`gateway-audit.jsonl`).

## 14. Pinned offline forum check (`013`)

A target profile can bind a catalog item to the Quarkus forum snapshot using an exact base commit, write scopes, and an external Gradle acceptance test. Run the offline Feature 013 drill with fake inference:

```bash
demo/.local/venv/bin/python demo/tests/qualify_forum_build.py
# Or skip telemetry export:
demo/.local/venv/bin/python demo/tests/qualify_forum_build.py --no-telemetry
```

The script checks out commit `37417ab` in `demo/.local/factory/agents/aeion-autonomous-forum`, runs an injected fake-model builder, executes `gradle test --offline` with external acceptance tests, simulates two review votes, and verifies the resulting `factory.build` span in Langfuse. This confirms the pipeline offline without spending inference quota, opening a remote PR, or deploying code. See `demo/forum-app/DOCKER.md` in the product repo for container build instructions.
