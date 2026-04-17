"""SQLite persistence for the prototype console."""

from __future__ import annotations

import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from .models import BotInput, LogInput


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    init_db(conn)
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS bots (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          status TEXT NOT NULL,
          allowed_user_ids TEXT NOT NULL DEFAULT '',
          provider_base_url TEXT NOT NULL DEFAULT '',
          provider_model TEXT NOT NULL DEFAULT '',
          system_prompt TEXT NOT NULL DEFAULT '',
          channel_secret_ref TEXT NOT NULL DEFAULT '',
          provider_secret_ref TEXT NOT NULL DEFAULT '',
          created_at INTEGER NOT NULL,
          updated_at INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS activity_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          bot_id TEXT NOT NULL,
          created_at INTEGER NOT NULL,
          telegram_user_id TEXT NOT NULL DEFAULT '',
          user_request TEXT NOT NULL DEFAULT '',
          assistant_response TEXT NOT NULL DEFAULT '',
          provider TEXT NOT NULL DEFAULT '',
          model TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'ok',
          error TEXT NOT NULL DEFAULT '',
          FOREIGN KEY (bot_id) REFERENCES bots(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()


def _now() -> int:
    return int(time.time())


def _bot_public(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "name": row["name"],
        "status": row["status"],
        "allowed_user_ids": row["allowed_user_ids"],
        "provider_base_url": row["provider_base_url"],
        "provider_model": row["provider_model"],
        "system_prompt": row["system_prompt"],
        "channel_secret_ref": row["channel_secret_ref"],
        "provider_secret_ref": row["provider_secret_ref"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def _log_public(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "bot_id": row["bot_id"],
        "created_at": row["created_at"],
        "telegram_user_id": row["telegram_user_id"],
        "user_request": row["user_request"],
        "assistant_response": row["assistant_response"],
        "provider": row["provider"],
        "model": row["model"],
        "status": row["status"],
        "error": row["error"],
    }


def create_bot(conn: sqlite3.Connection, data: BotInput) -> dict[str, Any]:
    now = _now()
    bot_id = f"bot-{uuid.uuid4().hex[:12]}"
    conn.execute(
        """
        INSERT INTO bots (
          id, name, status, allowed_user_ids, provider_base_url, provider_model,
          system_prompt, channel_secret_ref, provider_secret_ref, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bot_id,
            data.name,
            "stopped",
            data.allowed_user_ids,
            data.provider_base_url,
            data.provider_model,
            data.system_prompt,
            data.channel_secret_ref,
            data.provider_secret_ref,
            now,
            now,
        ),
    )
    conn.commit()
    bot = get_bot(conn, bot_id)
    assert bot is not None
    return bot


def list_bots(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute("SELECT * FROM bots ORDER BY created_at, id").fetchall()
    return [_bot_public(row) for row in rows]


def get_bot(conn: sqlite3.Connection, bot_id: str) -> dict[str, Any] | None:
    row = conn.execute("SELECT * FROM bots WHERE id = ?", (bot_id,)).fetchone()
    return _bot_public(row) if row else None


def set_bot_status(conn: sqlite3.Connection, bot_id: str, status: str) -> dict[str, Any] | None:
    conn.execute(
        "UPDATE bots SET status = ?, updated_at = ? WHERE id = ?",
        (status, _now(), bot_id),
    )
    conn.commit()
    return get_bot(conn, bot_id)


def set_bot_secret_refs(
    conn: sqlite3.Connection,
    bot_id: str,
    *,
    channel_secret_ref: str,
    provider_secret_ref: str,
) -> dict[str, Any] | None:
    conn.execute(
        """
        UPDATE bots
        SET channel_secret_ref = ?, provider_secret_ref = ?, updated_at = ?
        WHERE id = ?
        """,
        (channel_secret_ref, provider_secret_ref, _now(), bot_id),
    )
    conn.commit()
    return get_bot(conn, bot_id)


def add_log(conn: sqlite3.Connection, bot_id: str, data: LogInput) -> dict[str, Any] | None:
    if get_bot(conn, bot_id) is None:
        return None
    cur = conn.execute(
        """
        INSERT INTO activity_logs (
          bot_id, created_at, telegram_user_id, user_request, assistant_response,
          provider, model, status, error
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            bot_id,
            _now(),
            data.telegram_user_id,
            data.user_request,
            data.assistant_response,
            data.provider,
            data.model,
            data.status,
            data.error,
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM activity_logs WHERE id = ?", (cur.lastrowid,)).fetchone()
    return _log_public(row) if row else None


def list_logs(conn: sqlite3.Connection, bot_id: str) -> list[dict[str, Any]] | None:
    if get_bot(conn, bot_id) is None:
        return None
    rows = conn.execute(
        "SELECT * FROM activity_logs WHERE bot_id = ? ORDER BY created_at, id",
        (bot_id,),
    ).fetchall()
    return [_log_public(row) for row in rows]
