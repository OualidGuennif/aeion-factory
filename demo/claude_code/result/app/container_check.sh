#!/usr/bin/env bash
# Spec: knowledge/components/idea-board-runtime.md
# The container's acceptance run: each check prints "ok <name>" or stops with "FAIL <name>"; the stack,
# its volume and the scratch build context are removed at the end either way.
set -euo pipefail
cd "$(dirname "$0")"
URL=http://localhost:8000
SCRATCH=$(mktemp -d)
trap 'docker compose down -v >/dev/null 2>&1; rm -rf "$SCRATCH"' EXIT

ok() { echo "ok $1"; }
fail() {
  echo "FAIL $1" >&2
  exit 1
}

# The compose health check is the judge; curl here only reads what it already approved.
wait_healthy() {
  for _ in $(seq 1 30); do
    [ "$(docker compose ps --format '{{.Health}}' web)" = healthy ] && return 0
    sleep 1
  done
  return 1
}

# A stale volume from an earlier run would make "survives restart" pass for the wrong reason.
docker compose down -v >/dev/null 2>&1
docker compose up -d --build --quiet-pull >/dev/null 2>&1
wait_healthy || fail healthy
curl -sf "$URL/api/health" | grep -q '"status":"ok"' || fail healthy
ok healthy

[ "$(docker compose exec -T web id -u)" != 0 ] || fail non-root
ok non-root

# No env file, no local KV data and no curl inside the image.
docker compose exec -T web sh -c 'ls -A /app | grep -q "^\.env" && exit 1; test ! -e /app/data && ! command -v curl' ||
  fail "clean context"
ok "clean context"

curl -sf -X POST "$URL/api/ideas" -H 'content-type: application/json' -d '{"title":"Survives restart"}' >/dev/null ||
  fail "survives restart"
docker compose down >/dev/null 2>&1
docker compose up -d >/dev/null 2>&1
wait_healthy || fail "survives restart"
curl -sf "$URL/api/ideas" | grep -q '"title":"Survives restart"' || fail "survives restart"
ok "survives restart"

# A specifier the lock does not hold must stop the build at the install step.
cp Dockerfile deno.json deno.lock "$SCRATCH"/
sed -i.bak 's#"jsr:@std/ulid@^1.0.0"#"jsr:@std/ulid@^1.0.1"#' "$SCRATCH/deno.json"
grep -q 'ulid@^1.0.1' "$SCRATCH/deno.json" || fail "frozen lock"
if build_log=$(docker build --progress=plain "$SCRATCH" 2>&1); then fail "frozen lock"; fi
grep -qi "lockfile" <<<"$build_log" || fail "frozen lock"
ok "frozen lock"
