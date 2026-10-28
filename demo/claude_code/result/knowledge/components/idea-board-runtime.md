---
type: Component
title: "Idea Board runtime"
description: "The container that runs the production build: a pinned Deno image, a non-root user, a health check and a named volume for KV."
status: draft
generated:
  by: aeion-factory/1.3
  at: 2026-10-28
sources:
  - id: dockerfile
    resource: ../../app/Dockerfile
    title: "The image: locked install, one build, non-root run"
  - id: dockerignore
    resource: ../../app/.dockerignore
    title: "What never enters the build context"
  - id: compose
    resource: ../../app/compose.yaml
    title: "The web service, its health check and its volume"
  - id: check
    resource: ../../app/container_check.sh
    title: "The container's acceptance run"
  - id: serve
    resource: ../../app/serve.ts
    title: "The production entry point (PORT, default 8000)"
---

# Idea Board runtime

## Intent
One command, `docker compose up`, runs the production build of the board on port 8000. The container
is healthy only when the app answers, and the ideas survive a restart.

## Data sources
- `denoland/deno:2.9.8`, the official image at the latest stable Deno (2026-10-21), the same version
  the app is developed with.
- `deno.lock`: the exact dependency versions the image installs.
- The named volume `ideas-data` on `/data`: the KV file `KV_PATH=/data/ideas.sqlite3`.

## Inputs
- `app/` as the build context, minus what `.dockerignore` names: `.env*`, `data/`, `node_modules/`,
  `_fresh/`, `.DS_Store`.
- `PORT` (default 8000) and `KV_PATH`, set by `compose.yaml`.

## Outputs
| Command | Result |
| --- | --- |
| `docker compose up -d --build` | the `web` service, healthy within 30 s |
| `curl localhost:8000/api/health` | `{"status":"ok","version":"…"}` |
| `docker compose down && docker compose up -d` | the same ideas as before `down` |
| `docker compose down -v` | the container and the volume removed |

## Invariants
1. The container runs as the image's non-root `deno` user. Test: `app/container_check.sh` "non-root".
2. The health check runs with the app's own runtime (`deno eval` and `fetch`), so no `curl` is added
   to the image. Test: `app/container_check.sh` "healthy".
3. Ideas written before `down` are read after `up`. Test: `app/container_check.sh` "survives restart".
4. The image installs with `deno install --frozen`: a dependency change without its lock update fails
   the build. Test: `app/container_check.sh` "frozen lock".
5. No `.env` file and no KV data enter the image. Test: `app/container_check.sh` "clean context".

## Determinism
deterministic: a pinned base image and a frozen lock file.

## Acceptance checks
```bash
cd app && ./container_check.sh    # every check prints ok, then the stack and volume are removed
```

## Out of scope
- A registry push, TLS, a reverse proxy.
- More than one replica: Deno KV on a local SQLite file has one writer.
