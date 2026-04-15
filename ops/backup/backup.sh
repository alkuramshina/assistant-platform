#!/bin/sh
set -eu

read_secret() {
  var_name="$1"
  file_var_name="${var_name}_FILE"

  eval "value=\${${var_name}:-}"
  eval "file_path=\${${file_var_name}:-}"

  if [ -z "${value}" ] && [ -n "${file_path}" ] && [ -f "${file_path}" ]; then
    value="$(cat "${file_path}")"
  fi

  export "${var_name}=${value}"
}

read_secret RESTIC_PASSWORD
read_secret AWS_ACCESS_KEY_ID
read_secret AWS_SECRET_ACCESS_KEY

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
