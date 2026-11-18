# Æion Factory cockpit and model lab

This local pilot connects OpenTelemetry, Langfuse, Hindsight 1.2.0, and local SHA-256 checkpoints around Flue + Pi agent sessions. The cockpit and controller are Python processes running directly on the host. The agent harness uses Flue 2.3.1 on Pi 1.5.2 across [three execution tiers](#three-execution-tiers): in-memory triage in an emulated shell, a guided local assistant with folder-confined file tools, and autonomous coding whose tool calls run inside NVIDIA OpenShell 0.1.8. Generated code from both coding tiers is verified in OpenShell.

The product under test is the Agora forum (Quarkus/Java); the older Deno/Hono playground is gone. The canonical product source lives in the separate `aeion-autonomous-forum` checkout at `demo/.local/factory/agents/aeion-autonomous-forum`. Meanwhile, `demo/forum-app/` holds a read-only snapshot of that repository at the commit pinned in `demo/forum/source.json`, with file digests recorded in `demo/forum/source.lock.json`. Running `python3 demo/forum/source.py --check` rejects hand edits or extra tracked files, and `--refresh --product <checkout>` re-copies the pinned commit. All UI views follow Æion Spec's monochrome palette (`demo/app/theme.css`) using system typography, paginate long lists (10 features per page in the catalog, 5 runs or builds per page), and separate controls cleanly with a left sidebar.

Completed and in-progress features stay disabled so duplicate launches are blocked. The 100-spec catalog targets Quarkus, PostgreSQL, and React web. Dependencies unlock only after their current contract reaches the product `main` branch, while historical results from older spec revisions remain visible for reference without certifying newer specs. Live mode prepares acceptance contracts automatically. Read [current work](../work/current.md) for current delivery state, holds, and open transitions.

## Start a feature from the cockpit

1. Open [Feature cockpit](http://127.0.0.1:8088/) (also served at `/factory`) and unlock it with the private local token in `demo/.local/factory/admin.token`.
2. Switch filters or pages in the Catalog section, tick one **Ready** specification, inspect its Markdown if needed, and click **Build selected**.
3. Switch to the **Builds** section to follow the stages (`Prepare -> Build -> Check -> Review -> PR / CI -> Main`), inspect build evidence (failure codes, protected check results, review votes, and PR/CI links), or open the metadata-only session in Langfuse.
4. Pick newly unlocked specifications once their prerequisites reach `main`. The badge **Waiting for prerequisites** lists the missing dependency IDs cleanly rather than assuming strict numeric order.

A global execution pause is separate from a dependency wait. The controller owns task freezing, sandbox qualification, acceptance preparation, and publication. Failed attempts keep their trace and file history, and unknown costs or remote side effects pause for reconciliation rather than retrying automatically. Do not clear checks or mark features done just to unlock selection. Product demo URLs stay `Not deployed yet` until an actual deployment verification runs against `main`.

## Agora factory planning

The [Agora product plan](forum/PLAN.md), [factory contract](forum/ECOSYSTEM.md), and [100 feature specs](forum/features/README.md) define the target application. The [DeepSeek handoff](forum/DEEPSEEK_HANDOFF.md) lays out the build sequence, and [validation](forum/VALIDATION.md) separates catalog validation from runtime qualification. Fake inference stays the default so live runs and remote publishing remain explicit opt-ins.

The historical product snapshot is a Quarkus 3.40.1 / Java 25.0.4 service built with Gradle, carrying features 001 through 003 (skeleton and settings, migration runner, test harness), accounts, sessions, and threads backed by Kafka behind a transactional outbox, CSRF tokens on mutations, and 47 JUnit tests. `demo/forum-db/` wraps SQLite WAL backups (`VACUUM INTO`), restore verification, and single-writer leasing. `demo/forum-mobile/` contains an earlier Expo SDK 58 / React Native 0.88.1 client that typechecks and bundles 619 iOS modules; it is kept only as a historical mobile snapshot and does not reflect the current React DOM web roadmap.

For local container runs, the product repository includes a multi-stage Dockerfile and Compose definition (`demo/forum-app/DOCKER.md`). It binds only `127.0.0.1:8081`, stores SQLite in a named volume, and refuses to start without an ephemeral `AGORA_SESSION_SECRET`. The image is never pushed automatically; remote hosting stays a separate decision.

## Start and inspect

Run these commands from the repository root with Docker running, Python 3.11+, and Node.js 22.19+. The native OpenShell gateway bootstrap supports macOS arm64 and Linux x86_64/arm64. Ensure your Docker VM has enough memory for the eight observation containers plus transient sandboxes (an 8 GB shared Docker VM can slow down under heavy load).

```sh
python3 demo/setup.py --opencode-env /absolute/path/to/AEion/.env
python3 demo/install.py
python3 demo/openshell/setup.py
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml up -d --build
demo/.local/venv/bin/python demo/tests/qualify_flue.py
python3 demo/run.py
```

Omit `--opencode-env` when running simulation mode only. Setup copies `OPENCODE_API_KEY` into `demo/.local/stack.env` (owner-only permissions) without mounting your original `.env` or printing secrets, and refuses to overwrite existing credentials. Never print or commit `demo/.local/stack.env`, and never run `docker compose config` without `--quiet`. Running `install.py` builds the Python venv, fetches pinned tokenizers, and runs `npm ci` for the locked Flue harness.

GitHub credentials follow [`../.env.example`](../.env.example) and [runbook §5.1](factory/runbook.md#51-credentials-one-key-per-role): build, publish, and release are separate tokens, and no agent process ever holds more than its own scope.

| View | Local address | Purpose |
| --- | --- | --- |
| Feature cockpit | [localhost:8088](http://localhost:8088) | Paginated catalog, active and historical builds, daily budget, and environments |
| Model lab | [localhost:8088/lab](http://localhost:8088/lab) | Sandbox runner, paginated run history, model comparison, checkpoints, and stack health |
| Feature factory alias | [localhost:8088/factory](http://localhost:8088/factory) | Direct route to the Feature cockpit |
| Product demo | Shown only after deploy checks | Separate product checkout and deployment verification |
| Langfuse | [localhost:3300](http://localhost:3300) | Metadata traces, generations, usage estimates, and boolean scores |
| Hindsight | [localhost:9999](http://localhost:9999) | Session-analysis memory banks and semantic recall |

To sign in to Langfuse, read `LANGFUSE_EMAIL` and `LANGFUSE_PASSWORD` locally from `demo/.local/stack.env` in your editor; never paste credentials into chat or logs. The OTel collector binds loopback only for the host controller. Compose launches the eight observation services, while the forum build tools, feature controller, and Flue harness run on the host without exposing any repository folder or Docker socket to sandboxes.

Execution mode is explicit. The default `simulator` simulates build diffs and labels them as synthetic in the UI. `AEION_FACTORY_EXECUTION=offline` runs the pinned forum profile against deterministic offline fixtures (real base, real write scopes, real protected check, zero model calls). `AEION_FACTORY_EXECUTION=live` enables automatic acceptance preparation, the shared model catalog, and the Flue/Pi tier 3 builder. Missing provider credentials halt builds as `provider_unconfigured` rather than silently simulating. Workers authorized on the shared router are `glm-5.3-flash`, `qwen-3.8-flash`, `deepseek-4.1-flash`, `claude-haiku-5.5` (2026-11-02), `gpt-6-luna` (2026-11-06), and `minimax-m3.1-flash` replacing `mistral-large-4` (2026-11-08). Display IDs translate to canonical wire IDs before every request.

Legacy Java candidate checks run inside a disposable Docker container with `--network none`, no Docker socket, no host home mount, and only the candidate tree plus read-only toolchain caches. A pre-flight probe records the image digest and confirms network isolation before running tests; missing images or failed probes hold with `sandbox_unqualified`. `demo/factory/baseline.py` verifies existing baseline features against hashed paths and an isolated test run so dependent features can unlock without synthetic receipts. Pinned targets reject unrelated features with `target_feature_mismatch`.

Current product checks compile production sources before running candidate unit tests in a separate workspace and grade HTTP/browser acceptance outside the app's PID and filesystem namespaces. Ephemeral PostgreSQL instances provide an isolated loopback database without sharing source code or database credentials with the verifier. Schema transitions, migrations, and React bundles use dedicated qualifications documented in the [execution contract](../knowledge/components/factory-flue.md).

A standard walkthrough in `/lab`:

1. Replay the 250k handover from the sidebar or Run a task section: synthetic usage crosses 230k/250k, writes `HANDOVER.md`, launches a fresh agent, and records telemetry across the local stack.
2. Run a Flue build by selecting an execution tier, a JavaScript exercise, and either Auto or one of five Go profiles. Coding tiers edit `src/pricing.js` (inside OpenShell on tier 3) and run 12 or 14 Deno checks in a fresh sandbox.
3. Compare models under identical tier, task, gate, and method versions in the Models section, declaring any manual help explicitly.
4. Inspect saved SHA-256 checkpoints, correlated JSONL logs, Hindsight notes, and Langfuse traces.

The synthetic replay never calls a model API or pretends to build real code, while `qualify_flue.py` tests the live CLI harness against local fake inference. Real runs and synthetic rows stay strictly separated.

## Execution boundary

| Layer | Where it runs | What it may do |
| --- | --- | --- |
| Cockpit, controller, relay | Host process on loopback | Owns API keys, accounts tokens and spend, writes MDs and audit logs |
| Flue + Pi harness (`demo/flue`) | Host child process with clean env | Holds only session-scoped relay and bridge tokens |
| Sandbox bridge (tier 3) | Host loopback with per-session token | Forwards nine fixed-argv file and shell commands into one sandbox |
| OpenShell sandbox | Docker driver, Landlock, network `none` | Unprivileged UID, single subpath mount, writes only `src/`, zero egress |

Model calls leave from the host through the counting relay, so sandboxes never need outbound network access. Flue's `local()` sandbox is never used because it provides no process or filesystem isolation. The adapter in `demo/flue/src/sandboxes/openshell.ts` follows Flue's sandbox-adapter interface cleanly without coupling OpenShell into upstream harness code.

## Three execution tiers

| Tier (`runtime`) | Tools and isolation | Tasks | Acceptance |
| --- | --- | --- | --- |
| 1 Triage (`flue-just-bash`) | Emulated in-memory shell via just-bash 3.6.0 with hardened limits and `submit_triage`; no network | `webhook-triage-v1` (8 synthetic events) | Controller compares submitted labels against frozen answers |
| 2 Local assistant (`flue-local`) | Read/write/edit confined to the run workspace under `src/`, symlinks refused, no shell, strict `local-change` skill | Four frozen JS contracts | Protected Deno checks in OpenShell; final check in a fresh sandbox |
| 3 Autonomous coding (`flue-openshell`) | OpenShell adapter providing bash/read/write/edit/grep/glob inside the container via the bridge | Same four JS contracts | Same as tier 2 |

All three tiers share the relay, 230k/250k/300k context limits, `HANDOVER.md`, metadata observer, JSONL audit, OTLP telemetry, and memory adapters. Tier 2 limits only the model-facing tools rather than host OS privileges, so use tier 3 for untrusted coding work. In tier 1, `submit_triage` validates IDs and labels atomically into `result.json` before controller validation, and `just-bash` provides an isolated in-memory shell without `curl`. Auto selection and KPIs shard cohorts by both tier and task; benchmark campaigns run exclusively on tier 3.

## Observation and memory stack

- **OpenTelemetry (`0.163.2`)** ships explicit allowlisted metadata spans and canonicalized log bodies, linking Deno HTTP verification spans via W3C `traceparent`. Flue's built-in OTel exporter is left disabled because it captures prompts and tool payloads; instead a metadata-only `observe()` subscriber feeds the controller.
- **Langfuse (`4.75.0`)** ingests OTLP/HTTP spans, maps harness USD estimates to generation costs, and records autonomous completion and check pass status as boolean scores. Cockpit verdicts update immediately even if async score ingestion lags.
- **Local SHA-256 checkpoints** replaced the retired `claude-mem` service (`work/validation.md`). Handovers persist verified checkpoint metadata on disk with digest deduplication and explicit `/api/memory/checkpoint/<id>` readback checks.
- **Hindsight (`1.2.0`)** stores descriptive run summaries in separate real and synthetic banks using local chunk extraction and RRF reranking with `HINDSIGHT_API_LLM_PROVIDER=none`, avoiding redundant model spending. Semantic recall remains purely advisory and never modifies policies, credentials, or gates.

## Model choice and cost accounting

The harness pins Flue 2.3.1 (`@flue/runtime`, `@flue/cli`), Pi `@earendil-works/pi-ai` 1.5.2, and an exact `package-lock.json` covering five paid Go profiles: GLM 5.3 Flash, DeepSeek V4.1 Flash, GLM 5.3, GLM 5.2, and MiniMax M3.1 Flash. Requests pass through a custom Pi provider targeting the local relay (`User-Agent` and `x-opencode-session` forwarded verbatim as required by OpenCode Go) with pinned official tokenizers and chat templates.

The four coding exercises test cart totals (12 checks), shipping rules, exact discount arithmetic, and cart normalization (14 checks each). **Compare all tasks & models** runs available profiles across all 4 tasks with 2 repetitions (40 runs across 5 profiles), rotating order and stopping at a `$2` campaign ceiling (`$0.10` per task) or any unknown usage, context overflow, or sandbox failure.

Auto model selection considers only comparable tier 3 evidence under `flue-openshell-v1` and the 250k active-context rule, requiring at least two completed runs, 100% autonomous pass rate, and complete positive cost/latency records. Interrupted or manual-rescue runs disqualify a cohort; GLM 5.3 Flash serves as the provisional default until enough comparable runs accrue. Cost figures use Go model rates and represent local harness estimates rather than provider invoices.

### Daily purses (`$150.00` max per scope)

`demo/factory/budget.py` maintains an append-only JSONL journal at `demo/.local/budget/ledger.jsonl` (`0600`) across two isolated scopes (`aeion-factory` and `aeion-autonomous-forum`). Each Europe/Paris day enforces `DAILY_LIMIT_USD` from [`demo/budget.conf`](budget.conf) (capped at `$150.00`), reserving exposure before calling a model and settling actual usage afterward. Corrupted, missing, or over-limit ledgers fail closed (`budget_unavailable` or `budget_config_invalid`).

`demo/budget.conf` also bounds each author execution (`AUTHOR_MAX_USD` <= `$50.00`), each review vote (`REVIEW_MAX_USD` <= `$1.00`), and author wall-clock time (`AUTHOR_TIMEOUT_MINUTES` between 5 and 180). Overrides via `AEION_<KEY>` follow the same code ceilings, and active admitted builds retain their frozen reservation across restarts. Inspect today's spend without making any model call:

```bash
python3 -m demo.factory.budget --ledger demo/.local/budget/ledger.jsonl
```

## Context handover: 230k to 250k to 300k

1. At 230k active input tokens (local count or native report), the controller writes and fsyncs `HANDOVER.md` with task state, artifact SHA-256, check status, and next steps before admitting another model request.
2. At 250k tokens, the relay refreshes `HANDOVER.md` and blocks forwarding. The harness exits, OpenShell deletes and reaps the sandbox, the controller verifies the Markdown digest, and a new Flue conversation starts from scratch (`compaction` disabled) with the handover file in its opening message.
3. The relay counts complete requests with pinned tokenizers (`tokenizers.json`), reserves output plus `20,000` framing tokens, and rejects >300k allocations before forwarding. Closed-tokenizer models (`qwen`, `haiku`) reserve cost bounds before launch and gate continuation from complete native API usage including cache reads/writes.

Only a session-scoped relay token reaches the harness while `OPENCODE_API_KEY` stays in the host controller. Harness stdout/stderr are discarded, Flue compaction errors halt the run, and subagent delegation via `task` is refused and audited. Exceeding 300k native context or diverging by >20k from local token counts fails the run and pauses live runs via `demo/.local/data/context.blocked` pending investigation.

## OpenShell qualification and protected checks

OpenShell allows volume mounts only via labeled Docker volumes (`aeion-openshell-work` backed by `demo/.local/work`), never arbitrary host paths. Setup verifies the agent UID (host user on Linux, `10001` under Docker Desktop on macOS), read-only root/workspace outside `src/`, hidden sibling run directories, `NetworkMode=none`, absent Docker socket, and `OPENSHELL_TELEMETRY_ENABLED=false`. Check cases reach Deno over stdin inside a fresh sandbox where no author agent ever ran.

Security leases expire every 24 hours; live mode invokes `ensure_openshell_security()` automatically within the final hour (`demo/openshell/qualify.py`). For continuous renewal while the controller is stopped, you can add a 6-hour cron entry:

```bash
crontab -e
```

```cron
0 */6 * * * cd /path/to/aeion-factory && demo/.local/venv/bin/python -c 'import sys; from pathlib import Path; sys.path.insert(0, "demo/app"); import settings; from sandbox import connection; connection()' >/dev/null 2>&1
```

If a gateway restart leaves orphaned sandboxes behind, `demo/openshell/reap.py --older-than 3600` performs a dry run and `--execute` cleans expired OpenShell containers only when `demo/.local/factory/factory.db` confirms no active build lease exists. Running `qualify_flue.py` binds the immutable agent image, UID, relay, bridge, and harness hashes (`package-lock.json`), blocking live execution whenever any of those files change.

## Evidence, verification, and logs

Every run keeps an owner-only, fsynced audit log before exporting spans, omitting raw prompts, code, completions, hidden reasoning, and headers. `otel-logs` rotates up to 5 MB across 3 files, and collector export queues remain bounded in memory so local audits survive backend outages.

```sh
demo/.local/venv/bin/python -m unittest discover -s demo/tests -v
(cd demo/flue && npm test)
demo/.local/venv/bin/python demo/tests/qualify_scenarios.py
demo/.local/venv/bin/python demo/tests/qualify_flue.py
python3 demo/verify_backend.py
python3 demo/verify_backend.py --synthetic
```

## Live status without opening receipts

Inspect an active feature build safely from `demo/` without exposing prompts, receipts, or secrets:

```sh
python3 -m factory.live_status --feature 001
python3 -m factory.live_status --feature 001 --feedback
python3 -m factory.live_status --protection
```

The default command confirms whether the loopback controller is listening, lists recent status phases, `--feedback` adds correction round counts and failed CI check names (counting other feedback without printing reviewer prose), and `--protection` reports GitHub branch protection checks via the isolated release role.

## Stop cleanly and keep state

```sh
docker compose --env-file demo/.local/stack.env -f demo/compose.yaml down
```

Wait for active runs to finish before stopping the cockpit with `Ctrl-C`. State remains under `demo/.local/data` and `demo/.local/work` (capped at 100 stored lab runs). Use `down --volumes` only when intentionally wiping local databases; never regenerate `stack.env` while keeping old database volumes. Shut down the native OpenShell gateway via SIGTERM to the PID recorded in `demo/.local/openshell/` rather than pruning unrelated containers.
