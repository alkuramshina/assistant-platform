"""CLI entry point for the console API."""

from __future__ import annotations

import argparse

from .api import serve


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Nanobot Console API")
    parser.add_argument("--db", default="console.db", help="SQLite database path")
    parser.add_argument("--bot-root", default=None, help="Bot project root, default: DB directory/bots")
    parser.add_argument("--secret-root", default=None, help="Secret root, default: DB directory/secrets")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host, default: 127.0.0.1")
    parser.add_argument("--port", type=int, default=8787, help="Bind port, default: 8787")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    serve(args.db, args.host, args.port, args.bot_root, args.secret_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
