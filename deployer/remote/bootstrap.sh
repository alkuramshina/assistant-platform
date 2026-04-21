#!/usr/bin/env bash
set -eu

MODE="${1:-probe}"
REMOTE_ROOT="${2:-/opt/nanobot-console}"
CONSOLE_PORT="${3:-8787}"
CONSOLE_DOMAIN="${4:-}"
SERVICE_NAME="nanobot-console"

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

  if sudo -n true >/dev/null 2>&1; then
    printf 'sudo=ok\n'
  else
    printf 'sudo=password_required\n'
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

require_sudo() {
  if ! sudo -n true >/dev/null 2>&1; then
    printf 'error=sudo_password_required\n' >&2
    printf 'run interactively with a sudo password, configure non-interactive sudo by policy, or use a user that can sudo non-interactively\n' >&2
    return 1
  fi
}

install_prereqs() {
  require_sudo

  if has_cmd docker && docker compose version >/dev/null 2>&1; then
    return 0
  fi

  if has_cmd apt-get; then
    sudo apt-get update
    sudo apt-get install -y bash ca-certificates curl python3 docker.io

    if docker compose version >/dev/null 2>&1 || has_cmd docker-compose; then
      return 0
    fi

    for compose_pkg in docker-compose-plugin docker-compose-v2 docker-compose; do
      if apt-cache show "$compose_pkg" >/dev/null 2>&1; then
        sudo apt-get install -y "$compose_pkg" || true
        if docker compose version >/dev/null 2>&1 || has_cmd docker-compose; then
          return 0
        fi
      fi
    done

    printf 'error=compose_install_failed\n' >&2
    return 1
  fi

  printf 'error=unsupported_package_manager\n' >&2
  return 1
}

console_bind_host() {
  if [ -n "$CONSOLE_DOMAIN" ]; then
    printf '127.0.0.1'
  else
    printf '0.0.0.0'
  fi
}

install_caddy_if_needed() {
  if has_cmd caddy; then
    return 0
  fi
  if ! has_cmd apt-get; then
    printf 'error=caddy_install_unsupported_package_manager\n' >&2
    return 1
  fi
  sudo apt-get update
  if ! apt-cache show caddy >/dev/null 2>&1; then
    printf 'error=caddy_package_missing\n' >&2
    return 1
  fi
  sudo apt-get install -y caddy
}

configure_https_proxy() {
  if [ -z "$CONSOLE_DOMAIN" ]; then
    printf 'warning=http_only_console\n'
    return 0
  fi

  install_caddy_if_needed
  printf 'https_proxy=configure\n'
  sudo tee /etc/caddy/Caddyfile >/dev/null <<EOF
$CONSOLE_DOMAIN {
  reverse_proxy 127.0.0.1:$CONSOLE_PORT
}
EOF
  if has_cmd systemctl; then
    sudo systemctl enable caddy
    sudo systemctl reload caddy || sudo systemctl restart caddy
  fi
  printf 'https_proxy=caddy\n'
}

apply() {
  require_sudo
  install_prereqs
  sudo mkdir -p \
    "$REMOTE_ROOT" \
    "$REMOTE_ROOT/app" \
    "$REMOTE_ROOT/bin" \
    "$REMOTE_ROOT/bots" \
    "$REMOTE_ROOT/secrets" \
    "$REMOTE_ROOT/templates" \
    "$REMOTE_ROOT/logs"
  sudo chmod 0755 "$REMOTE_ROOT"
  sudo chmod 0700 "$REMOTE_ROOT/secrets"
  printf 'remote_root=%s\n' "$REMOTE_ROOT"
  printf 'apply=ok\n'
}

finalize() {
  require_sudo

  if [ ! -d "$REMOTE_ROOT/app/console" ]; then
    printf 'error=app_not_uploaded\n' >&2
    return 1
  fi

  if has_cmd docker; then
    printf 'docker_daemon=check\n'
    sudo docker info >/dev/null
    printf 'docker_build=start\n'
    sudo docker build -t nanobot-enterprise-pilot:dev "$REMOTE_ROOT/app"
    printf 'docker_build=ok\n'
  else
    printf 'docker_build=skipped_no_docker\n'
  fi

  if has_cmd systemctl; then
    CONSOLE_BIND_HOST="$(console_bind_host)"
    printf 'service_unit=write\n'
    sudo tee "/etc/systemd/system/$SERVICE_NAME.service" >/dev/null <<EOF
[Unit]
Description=Nanobot Console
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$REMOTE_ROOT/app
ExecStart=/usr/bin/python3 -m console --db $REMOTE_ROOT/console.db --bot-root $REMOTE_ROOT/bots --secret-root $REMOTE_ROOT/secrets --host $CONSOLE_BIND_HOST --port $CONSOLE_PORT
Restart=unless-stopped
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
    printf 'service_daemon_reload=start\n'
    sudo systemctl daemon-reload
    printf 'service_enable=start\n'
    sudo systemctl enable "$SERVICE_NAME"
    printf 'service_restart=start\n'
    sudo systemctl restart "$SERVICE_NAME"
    printf 'service=%s\n' "$SERVICE_NAME"
    printf 'service_status=%s\n' "$(systemctl is-active "$SERVICE_NAME" 2>/dev/null || printf unknown)"
  else
    printf 'service=systemd_missing\n'
  fi

  configure_https_proxy
  if [ -n "$CONSOLE_DOMAIN" ]; then
    printf 'console_url=https://%s/\n' "$CONSOLE_DOMAIN"
    printf 'console_backend=http://127.0.0.1:%s/\n' "$CONSOLE_PORT"
  else
    printf 'console_url=http://SERVER:%s/\n' "$CONSOLE_PORT"
  fi
  printf 'finalize=ok\n'
}

case "$MODE" in
  probe)
    probe
    ;;
  apply)
    apply
    ;;
  finalize)
    finalize
    ;;
  *)
    printf 'usage: %s probe|apply|finalize [/opt/nanobot-console] [8787] [console.example.com]\n' "$0" >&2
    exit 2
    ;;
esac
