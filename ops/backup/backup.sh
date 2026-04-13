#!/bin/sh
set -eu

: "${RESTIC_REPOSITORY:?RESTIC_REPOSITORY is required}"
: "${RESTIC_PASSWORD:?RESTIC_PASSWORD is required}"

APP_NAME="${APP_NAME:-nanobot-pilot}"

restic snapshots >/dev/null 2>&1 || restic init

restic backup /backup/nanobot_data /backup/nanobot_workspace \
  --tag "${APP_NAME}" \
  --tag docker-volume

restic forget \
  --tag "${APP_NAME}" \
  --keep-last 7 \
  --keep-daily 7 \
  --keep-weekly 4 \
  --prune
