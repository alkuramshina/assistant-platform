#!/usr/bin/env bash
set -euo pipefail

export NANOBOT_HOME="${NANOBOT_HOME:-/home/app/.nanobot}"
export NANOBOT_CONFIG="${NANOBOT_CONFIG:-${NANOBOT_HOME}/config.json}"
export NANOBOT_WORKSPACE="${NANOBOT_WORKSPACE:-/workspace}"
export NANOBOT_GATEWAY_PORT="${NANOBOT_GATEWAY_PORT:-18790}"

mkdir -p "${NANOBOT_HOME}" "${NANOBOT_WORKSPACE}"

python /app/generate_config.py

exec nanobot gateway --config "${NANOBOT_CONFIG}" --workspace "${NANOBOT_WORKSPACE}" --port "${NANOBOT_GATEWAY_PORT}"
