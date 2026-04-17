#!/bin/sh
set -eu

MODE="${1:-probe}"
REMOTE_ROOT="${2:-/opt/nanobot-console}"

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

probe() {
  printf 'os=%s\n' "$(uname -s 2>/dev/null || printf unknown)"
  printf 'arch=%s\n' "$(uname -m 2>/dev/null || printf unknown)"

  if [ -r /etc/os-release ]; then
    . /etc/os-release
    printf 'distro=%s\n' "${ID:-unknown}"
    printf 'version=%s\n' "${VERSION_ID:-unknown}"
  else
    printf 'distro=unknown\n'
    printf 'version=unknown\n'
  fi

  if has_cmd docker; then
    printf 'docker=ok\n'
    printf 'docker_version=%s\n' "$(docker --version 2>/dev/null | sed 's/[[:space:]]/ /g')"
  else
    printf 'docker=missing\n'
  fi

  if docker compose version >/dev/null 2>&1; then
    printf 'compose=ok\n'
    printf 'compose_version=%s\n' "$(docker compose version 2>/dev/null | sed 's/[[:space:]]/ /g')"
  elif has_cmd docker-compose; then
    printf 'compose=ok\n'
    printf 'compose_version=%s\n' "$(docker-compose --version 2>/dev/null | sed 's/[[:space:]]/ /g')"
  else
    printf 'compose=missing\n'
  fi

  printf 'disk_kb=%s\n' "$(df -Pk / 2>/dev/null | awk 'NR==2 {print $4}')"
  printf 'memory_kb=%s\n' "$(awk '/MemTotal/ {print $2}' /proc/meminfo 2>/dev/null || printf unknown)"

  if has_cmd curl && curl -fsI --max-time 5 https://github.com >/dev/null 2>&1; then
    printf 'network=ok\n'
  elif has_cmd wget && wget -q --spider --timeout=5 https://github.com >/dev/null 2>&1; then
    printf 'network=ok\n'
  else
    printf 'network=unknown\n'
  fi
}

install_prereqs() {
  if has_cmd docker && docker compose version >/dev/null 2>&1; then
    return 0
  fi

  if has_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl docker.io docker-compose-plugin
    return 0
  fi

  printf 'error=unsupported_package_manager\n' >&2
  return 1
}

apply() {
  install_prereqs
  sudo mkdir -p \
    "$REMOTE_ROOT" \
    "$REMOTE_ROOT/bin" \
    "$REMOTE_ROOT/bots" \
    "$REMOTE_ROOT/templates" \
    "$REMOTE_ROOT/logs"
  sudo chmod 0755 "$REMOTE_ROOT"
  printf 'remote_root=%s\n' "$REMOTE_ROOT"
  printf 'apply=ok\n'
}

case "$MODE" in
  probe)
    probe
    ;;
  apply)
    apply
    ;;
  *)
    printf 'usage: %s probe|apply [/opt/nanobot-console]\n' "$0" >&2
    exit 2
    ;;
esac
