# Synthetic examples

Try the bundled calculation with Python 3.9+ and no provider account:

```sh
python3 examples/compare_cohorts.py
python3 examples/validate_fixtures.py
python3 -m unittest discover -s tests -v
```

`compare_cohorts.py` prints fictional cohort summaries. It includes failed and assisted costs, keeps unknown quality explicit, and returns an undefined ratio when zero autonomous tasks succeed. It never controls a session or ranks real models. See the regression tests under `tests/`.

`validate_fixtures.py` rejects duplicate JSON object keys, non-finite numbers, and mismatched policy, task/run, artifact/check, or charge references. It preserves the example's disabled observe/shadow controls and deduplicates identical redeliveries by producer, boot ID, and event ID, while rejecting conflicting duplicates. It covers only these fictional fixtures rather than production events, provider behavior, privacy enforcement, or real task runs.

Every record here is synthetic, marked `example_only: true`, and uses proposed Æion contracts. There are no live credentials, captured prompts, production task IDs, or executed provider results. Repeated hexadecimal digests show identity binding cleanly without hashing real source files.

| File | Purpose |
| --- | --- |
| [Run manifest](run-manifest.json) | One observe-only evaluation run, fixed baseline, and capture/limit scope |
| [Routing policy](routing-policy.json) | Shadow-only catalog covering API and subscription paths with actuation off |
| [Session events](session-events.jsonl) | Retry, duplicate delivery, missing usage, late reconciliation, and verified outcome |
| [Task outcome](task-outcome.json) | Artifact-bound acceptance with intervention coverage and inference-only cost scope |
| [Provider request fragments](provider-requests.json) | API field shapes with unresolved model and provider placeholders |
| [Cohort comparison](cohort-comparison.json) | Worked cost, duration, and autonomy arithmetic across ten fictional tasks per policy |

The routing policy has no live-qualified profiles, quality floor, or exploration enabled, and nothing in a synthetic policy can alter the manifest's chosen baseline.

## Session and accounting example

The first inference attempt times out before reporting final usage, keeping exposure held. A second attempt with its own ID succeeds, while event `e07` arrives twice to test transport deduplication. When the first attempt reconciles later, inference spending adds up cleanly to `0.02 + 0.03 = 0.05 USD`: two charges rather than one combined call or `0.08 USD` from double-counting the duplicate. Before reconciliation completes, total cost stays unknown. That `0.05` figure covers inference only, not total task cost or provider billing guarantees.

On the second attempt, normalized input is 100 tokens (including 60 cached), and output is 20 tokens (including 5 reasoning). Subsets are not summed into totals (100, not 160; 20, not 25), and unknown cache-write counts stay `null` rather than guessing zero.

## Why the cheapest call can lose

Both policies in [`cohort-comparison.json`](cohort-comparison.json) run against the same ten fictional task IDs (`synthetic-01` through `synthetic-10`) with complete cost and outcome records. Human wages are excluded and corrective minutes stay separate. Request counts include retries, and p95 wall time uses nearest-rank ordering.

The calculation rejects cohorts with missing, extra, or swapped task IDs. Absent maturity or intervention-coverage fields keep quality and cost per success unknown.

| Measure | Cheap profile | Balanced profile |
| --- | --- | --- |
| Inference requests | 800 | 400 |
| Mean inference cost per request | $0.05 | $0.15 |
| Total inference | $40 | $60 |
| Sandbox | $20 | $12 |
| Evaluation | $10 | $8 |
| Observability | $2 | $2 |
| All-in cohort cost | $72 | $82 |
| Verified autonomous successes | 6/10 | 9/10 |
| Assisted successes | 2/10 | 0/10 |
| Failures | 2/10 | 1/10 |
| Corrective human minutes | 20 | 0 |
| p95 task wall time | 1,800 s | 600 s |
| Cost per autonomous success | $12.00 | $9.11 |

The balanced profile pays more per request and more overall (`$82` vs `$72`), yet costs less per autonomous pass (`$9.11` vs `$12.00`). This shows why the denominator matters; ten fictional tasks do not establish model quality or real savings.

Recompute from the Æion Factory root using standard Python:

```sh
python3 - <<'PY'
import json
from decimal import Decimal
from math import ceil
from pathlib import Path

data = json.loads(Path('examples/cohort-comparison.json').read_text())
assert data['example_only'] is True
for policy in data['policies']:
    tasks = policy['tasks']
    total = sum((Decimal(v) for t in tasks for v in t['costs'].values()), Decimal(0))
    inference = sum((Decimal(t['costs']['inference']) for t in tasks), Decimal(0))
    requests = sum(t['request_count'] for t in tasks)
    successes = sum(t['outcome'] == 'autonomous' for t in tasks)
    durations = sorted(t['wall_seconds'] for t in tasks)
    p95 = durations[ceil(0.95 * len(durations)) - 1]
    per_success = total / successes if successes else None
    print(policy['policy_id'], {
        'cohort_cost_usd': str(total),
        'inference_cost_per_request_usd': str(inference / requests),
        'autonomous_successes': successes,
        'cost_per_autonomous_success_usd': str(per_success),
        'p95_wall_seconds': p95,
    })
PY
```

## Request fragment limits

The OpenRouter and DeepInfra examples in [`provider-requests.json`](provider-requests.json) use documented Chat Completions field names with no authentication headers. Model slugs, pricing, and optional settings require separate qualification against a live endpoint.

`reasoning.exclude` in the OpenRouter fragment filters returned text without removing reasoning cost, and DeepInfra's optional cache or tier flags are not universal model capabilities. Do not forward these fragments unchanged to an Anthropic-compatible endpoint; see the [capability matrix](../knowledge/references/provider-capabilities.md).
