#!/usr/bin/env bash
set -eu

SERVICE_NAME="nanobot-console"
DEFAULT_REMOTE_ROOT="/opt/nanobot-console"
REMOTE_ROOT="${NANOBOT_CONSOLE_ROOT:-$DEFAULT_REMOTE_ROOT}"
CONSOLE_PORT="${NANOBOT_CONSOLE_PORT:-8787}"

usage() {
  cat <<EOF
Usage: $0 restart|status|logs|url

Commands:
  restart  Restart Nanobot Console
  status   Show service status
  logs     Show recent service logs
  url      Print the configured HTTP URL
EOF
}

host_ip() {
  hostname -I 2>/dev/null | awk '{print $1}'
}

case "${1:-}" in
  restart)
    sudo systemctl restart "$SERVICE_NAME"
    sudo systemctl status "$SERVICE_NAME" --no-pager
    ;;
  status)
    sudo systemctl status "$SERVICE_NAME" --no-pager
    ;;
  logs)
    sudo journalctl -u "$SERVICE_NAME" -n "${2:-80}" --no-pager
    ;;
  url)
    ip="$(host_ip)"
    if [ -n "$ip" ]; then
      printf 'http://%s:%s/\n' "$ip" "$CONSOLE_PORT"
    else
      printf 'http://SERVER:%s/\n' "$CONSOLE_PORT"
    fi
    ;;
  ""|-h|--help|help)
    usage
    ;;
  *)
    printf 'Unknown command: %s\n\n' "$1" >&2
    usage >&2
    exit 2
    ;;
esac
