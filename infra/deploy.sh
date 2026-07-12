#!/usr/bin/env bash
# Prod deploy on the VPS: sync main, pull the five ghcr images CI built, restart
# only what changed, health-check. Idempotent — safe to run by cron every ~5 min.
# One-time: docker login ghcr.io (PAT with read:packages) as the user cron runs as.
# Log: /opt/noxx-shop/deploy.log
set -uo pipefail
cd /opt/noxx-shop || exit 1

# single-flight: skip if a previous run is still going
exec 9>/tmp/noxx-deploy.lock
flock -n 9 || exit 0

log() { echo "$(date -Is) $*" >> /opt/noxx-shop/deploy.log; }
DC="docker compose -p infra --env-file .env -f infra/docker-compose.yml --project-directory infra"
SERVICES="backend bot media-server admin miniapp"

git fetch origin main -q 2>/dev/null && git merge --ff-only origin/main -q 2>/dev/null || true

if ! $DC pull -q $SERVICES 2>/dev/null; then
  log "FAILED pull (docker login ghcr.io done?)"
  exit 1
fi

up=$($DC up -d --no-build 2>&1)
changed=$(printf '%s\n' "$up" | grep -cE 'Started|Recreated|Created')
if [ "$changed" -eq 0 ]; then
  log "nochange $(git rev-parse --short HEAD)"
  exit 0
fi

ok=0
for _ in $(seq 1 24); do
  if curl -fsS -m5 http://localhost:8000/health >/dev/null 2>&1; then ok=1; break; fi
  sleep 5
done

if [ "$ok" = 1 ]; then
  log "ok $(git rev-parse --short HEAD) ${changed}chg"
else
  log "FAILED health $(git rev-parse --short HEAD)"
  exit 1
fi
