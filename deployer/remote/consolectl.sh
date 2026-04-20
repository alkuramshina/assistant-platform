#!/usr/bin/env bash
set -eu

SERVICE_NAME="nanobot-console"
DEFAULT_REMOTE_ROOT="/opt/nanobot-console"
REMOTE_ROOT="${NANOBOT_CONSOLE_ROOT:-$DEFAULT_REMOTE_ROOT}"
CONSOLE_PORT="${NANOBOT_CONSOLE_PORT:-8787}"

usage() {
  cat <<EOF
Usage: $0 restart|status|logs|bot-logs|url

Commands:
  restart  Restart Nanobot Console
  status   Show service status
  logs     Show recent service logs
  bot-logs Show recent logs for one bot: $0 bot-logs <bot-id> [lines]
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
  bot-logs)
    bot_id="${2:-}"
    if [ -z "$bot_id" ]; then
      printf 'Usage: %s bot-logs <bot-id> [lines]\n' "$0" >&2
      exit 2
    fi
    safe_id="$(printf '%s' "$bot_id" | sed 's/[^a-zA-Z0-9_-]/-/g' | sed 's/^-*//; s/-*$//' | cut -c1-64)"
    if [ -z "$safe_id" ]; then
      printf 'Invalid bot id: %s\n' "$bot_id" >&2
      exit 2
    fi
    project="nanobot_$(printf '%s' "$safe_id" | tr '-' '_')"
    compose="$REMOTE_ROOT/bots/$safe_id/docker-compose.yml"
    if [ ! -f "$compose" ]; then
      printf 'Compose file not found: %s\n' "$compose" >&2
      exit 1
    fi
    sudo docker compose -p "$project" -f "$compose" logs --timestamps --tail "${3:-120}"
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
