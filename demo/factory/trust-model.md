# Trust model: what a rogue agent can and cannot do

This document summarizes the mechanical limits placed on coding agents if the underlying model tries to act outside its task. Every boundary maps directly to enforcing code, along with explicit notes on what those checks do not guarantee.

## The core rule

Model outputs are always treated as untrusted data rather than authority. An agent can write source code inside its sandbox, but it cannot execute generated code on the host, bypass protected tests, widen its write scope, approve its own PR, or trigger a merge.

## 1. Generated code stays inside OpenShell

- Build tools run in OpenShell with `landlock=hard_requirement`, unprivileged UID (`10001`), `NetworkMode=none`, no Docker socket, and read-only system paths.
- Host Python processes only inspect files and compute hashes. `digest()` rejects symlinks, device nodes, and files above 32 KiB before reading contents.
- Protected acceptance checks run in a fresh sandbox (`role="check"`) seeded cleanly from the validated artifact rather than the author agent's container.

## 2. Diffs are validated structurally

`demo/factory/artifact.py` inspects the actual `git diff` and rejects the entire batch if any path leaves declared literal write scopes, uses absolute paths or `..`, touches `.git` metadata, introduces symlinks or non-regular files, or renames out of scope. Partial acceptance is never used.

## 3. File transport copies bytes only

`collect()` streams directory entries over the sandbox exec channel and `materialize()` writes plain files on the host, rejecting path traversal, backslashes, and locked targets (`SANDBOX_SYNC_TARGET_LOCKED`) without executing anything.

## 4. Protected checks stay unreachable

`demo/factory/checks.py` runs acceptance tests chosen by the host controller from a directory outside agent reach. Any missing required check returns `qualification_missing` rather than passing silently.

## 5. Deterministic rule checks run before LLM reviews

Even a second LLM produces untrusted output, so `demo/factory/review.py` applies deterministic rules over the bounded diff before any model reviewer runs:

| Finding | Decision |
| --- | --- |
| Out-of-scope path, empty diff, or invalid artifact | Refused |
| Credential patterns (`ghp_`, `sk-`, `AKIA`, private keys, Slack tokens) | Held |
| Destructive commands (`rm -rf /`, `curl ... \| sh`, `chmod 777`, `sudo`, `git push --force`, `npm publish`) | Held |
| Dependency manifest edits (`package.json`, lockfiles, `requirements.txt`) | Held |
| Binary files, file > 256 KiB, > 50 changed files, or total diff > 512 KiB | Held |

Rules are deterministic and bind a content digest so edits cannot reuse an older approval. Holds set `owner_review_required` and never publish.

## 6. Build agents stop on a local branch

`demo/factory/boundary.py` and the agent prompt in `demo/flue/src/agents/coder.ts` share the exact same five rules (verified by `test_factory_boundary.py`):

1. Work only inside the assigned workspace and declared write paths.
2. Commit only on your branch; push nothing, open no PR, merge nothing.
3. Never review your own changes.
4. Stop cleanly once checks pass or report blockers in `HANDOVER.md`.
5. Never poll for reviewers or merge on anyone's behalf.

Task instructions live in `TASK.md` outside the repository checkout. Freezing computes a tree digest verified again at push time so late commits after the freeze invalidate the receipt.

## 7. Two independent model families must approve

`demo/factory/review_circuit.py` enforces model diversity across the author and two reviewers:

- Both the author model and its provider family are excluded from review selection (`models.py`).
- Reviewer 1 and Reviewer 2 come from two distinct remaining families.
- Timeouts, HTTP errors, malformed replies, or rejections hold the run cleanly. Failures, rejected builds, or failing CI checks trigger at most two correction rounds on the original model (with bounded, sanitized feedback labels) followed by up to two attempts on fresh models before pausing for the owner.
- Complete changed diffs must fit within the 24,000-character review payload limit (`review_input_too_large`), preventing partial-excerpt approvals. Unknown author models pause before voting.
- Approvals bind whole-file coverage, tree digests, and parsed JSON verdicts directly into the build receipt.

Trace export checks stay strict as well: `Telemetry` reports `exported_unconfirmed` after collector handoff and reaches `confirmed` only after reading the trace back from Langfuse. Before pushing, `demo/factory/publisher.py::verified_receipt` re-verifies the passed gate, approved deterministic review, two approved circuit votes, and matching base and artifact digests.

## 8. Publishing is narrow and isolated

`demo/factory/publish.py` blocks forged issuers, mismatched repositories, cancelled builds, altered digests, or out-of-scope edits, and holds for manual approval whenever the diff touches sensitive paths (`auth`, `migrations`, `security`, `moderation`, `rules`, `runtime`, `deploy`, `permission`, or dependency files). Remote writes stay dry-run by default and require explicit `allow_merge` and `merge` flags once CI confirms the exact PR head.

Build workers never touch `GH_API_KEY`. Only `demo/factory/publisher.py` loads publish permissions after asserting that inference and release credentials are absent:

| Key | Role | GitHub permissions | Can it merge `main`? |
| --- | --- | --- | --- |
| `GH_BUILD_KEY` | Build | `contents:read`, `pull_requests:read` | No |
| `GH_API_KEY` | Publish | `contents:write`, `pull_requests:write` | Isolated publisher refuses merges |
| `GH_RELEASE_KEY` | Release | `contents:write`, `pull_requests:write`, `administration:read` | Isolated release process only after required evidence |
| `OPENCODE_API_KEY` | Inference | None | No |

`demo/factory/keys.py` enforces these role assertions (`assert_only()`, `assert_worker_isolated()`), `demo/app/settings.py` scrubs publish keys on startup, and `test_factory_keys.py` checks agreement with `.env.example`. Independently, branch protection on GitHub `main` and `develop` enforces pull requests, linear history, resolved review threads, and green checks (`Knowledge, links and repository health`, `Product artifacts`, `secret-scan`, `dependency-scan`, `sast-scan`), blocking direct pushes even from admins.

## 9. Hard payload bounds

Diffs cannot exceed 512 KiB, 50 files, or 256 KiB per file. Sandbox bridge payloads stop at 1 MiB and directory syncs at 8 MiB. Audit logs accept only allowlisted short scalar attributes (`INVALID_AUDIT_EVENT` on free-form text) and omit prompts, source code, and model responses.

## 10. Where human sign-off stays mandatory

- Sensitive paths, dependency manifests, and credential-shaped changes.
- All merges to protected branches, releases, and deployments.
- Every candidate reaches `main` only through an isolated branch and a reviewed pull request.

## Explicit limits

Deterministic rules catch dangerous patterns rather than arbitrary semantic bugs. A misbehaving model could still craft subtle buggy code that passes static filters, which is why branches stay isolated, protected tests are decoupled from the workspace, diffs stay small and content-addressed, and human owners retain control over pull requests and merges.
