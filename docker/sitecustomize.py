"""Optional console activity logging hook for the prototype image."""

from __future__ import annotations

import json
import os
import time
import urllib.request
from typing import Any


ACTIVITY_URL = os.environ.get("NANOBOT_CONSOLE_ACTIVITY_URL", "").strip()
BOT_ID = os.environ.get("NANOBOT_CONSOLE_BOT_ID", "").strip()
PROVIDER = os.environ.get("DEFAULT_PROVIDER", "").strip()
MODEL = os.environ.get("DEFAULT_MODEL", "").strip()


def _post_activity(payload: dict[str, Any]) -> None:
    if not ACTIVITY_URL:
        return
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        ACTIVITY_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        urllib.request.urlopen(request, timeout=3).close()
    except Exception:
        return


def _patch_telegram() -> None:
    if not ACTIVITY_URL:
        return

    try:
        from nanobot.channels.telegram import TelegramChannel
    except Exception:
        return

    original_handle = TelegramChannel._handle_message
    original_send = TelegramChannel.send
    pending: dict[str, dict[str, str]] = {}

    async def handle_with_capture(self, *args, **kwargs):
        sender_id = kwargs.get("sender_id", args[0] if len(args) > 0 else "")
        chat_id = kwargs.get("chat_id", args[1] if len(args) > 1 else "")
        content = kwargs.get("content", args[2] if len(args) > 2 else "")
        pending[str(chat_id)] = {
            "telegram_user_id": str(sender_id),
            "user_request": str(content),
        }
        return await original_handle(self, *args, **kwargs)

    async def send_with_activity(self, msg):
        await original_send(self, msg)
        metadata = getattr(msg, "metadata", {}) or {}
        if metadata.get("_progress", False):
            return
        chat_id = str(getattr(msg, "chat_id", ""))
        request_data = pending.pop(chat_id, {})
        payload = {
            "telegram_user_id": request_data.get("telegram_user_id", chat_id),
            "user_request": request_data.get("user_request", ""),
            "assistant_response": str(getattr(msg, "content", "") or ""),
            "provider": PROVIDER,
            "model": MODEL,
            "status": "ok",
            "error": "",
            "bot_id": BOT_ID,
            "created_at": int(time.time()),
        }
        _post_activity(payload)

    TelegramChannel._handle_message = handle_with_capture
    TelegramChannel.send = send_with_activity


_patch_telegram()
