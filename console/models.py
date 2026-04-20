"""Small DTO helpers for console records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class BotInput:
    name: str
    allowed_user_ids: str = ""
    provider_base_url: str = ""
    provider_model: str = ""
    proxy_url: str = ""
    system_prompt: str = ""
    channel_secret_ref: str = ""
    provider_secret_ref: str = ""
    channel_secret_value: str = ""
    provider_secret_value: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "BotInput":
        name = str(payload.get("name", "")).strip()
        if not name:
            raise ValueError("name is required")
        return cls(
            name=name,
            allowed_user_ids=str(payload.get("allowed_user_ids", "")).strip(),
            provider_base_url=str(payload.get("provider_base_url", "")).strip(),
            provider_model=str(payload.get("provider_model", "")).strip(),
            proxy_url=str(payload.get("proxy_url", "")).strip(),
            system_prompt=str(payload.get("system_prompt", "")).strip(),
            channel_secret_ref=str(payload.get("channel_secret_ref", "")).strip(),
            provider_secret_ref=str(payload.get("provider_secret_ref", "")).strip(),
            channel_secret_value=str(payload.get("channel_secret_value", "")).strip(),
            provider_secret_value=str(payload.get("provider_secret_value", "")).strip(),
        )


@dataclass(frozen=True)
class LogInput:
    telegram_user_id: str
    user_request: str
    assistant_response: str
    provider: str = ""
    model: str = ""
    status: str = "ok"
    error: str = ""

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "LogInput":
        return cls(
            telegram_user_id=str(payload.get("telegram_user_id", "")).strip(),
            user_request=str(payload.get("user_request", "")),
            assistant_response=str(payload.get("assistant_response", "")),
            provider=str(payload.get("provider", "")).strip(),
            model=str(payload.get("model", "")).strip(),
            status=str(payload.get("status", "ok")).strip() or "ok",
            error=str(payload.get("error", "")),
        )
