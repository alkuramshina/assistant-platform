"""Helpers for masking secrets before text reaches UI or logs."""

from __future__ import annotations

import re


REDACTED = "<redacted>"

PATTERNS = (
    # Telegram bot token: numeric bot id, colon, high-entropy token body.
    re.compile(r"\b\d{6,}:[A-Za-z0-9_-]{20,}\b"),
    # Common API key prefixes.
    re.compile(r"\b(sk-or-v1-[A-Za-z0-9_-]{20,})\b"),
    re.compile(r"\b(sk-[A-Za-z0-9_-]{20,})\b"),
)


def redact_secrets(text: str) -> str:
    redacted = text
    for pattern in PATTERNS:
        redacted = pattern.sub(REDACTED, redacted)
    return redacted
