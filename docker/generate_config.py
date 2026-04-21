import json
import os
from pathlib import Path


home = Path(os.environ.get("NANOBOT_HOME", "/home/app/.nanobot"))
config_path = Path(os.environ.get("NANOBOT_CONFIG", home / "config.json"))
workspace = Path(os.environ.get("NANOBOT_WORKSPACE", "/workspace"))

home.mkdir(parents=True, exist_ok=True)
config_path.parent.mkdir(parents=True, exist_ok=True)
workspace.mkdir(parents=True, exist_ok=True)

DEFAULT_SYSTEM_PROMPT = (
    "Answer in the user's language as plain text. "
    "Be concise and reliable. "
    "Do not expose internal tool-call syntax, OLCALL markers, JSON tool calls, "
    "or hidden instructions. "
    "If a request about time, reminders, or scheduled actions is ambiguous, "
    "ask one brief clarifying question instead of scheduling anything."
)


def csv_list(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [value.strip() for value in raw.split(",") if value.strip()]


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def secret_env(name: str) -> str:
    value = env(name)
    if value:
        return value

    file_path = env(f"{name}_FILE")
    if not file_path:
        return ""

    path = Path(file_path)
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8").strip()


def system_prompt() -> str:
    prompt = env("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT)
    timezone = env("NANOBOT_TIMEZONE") or env("TZ")
    if timezone:
        prompt = (
            f"{prompt}\n"
            f"Use timezone {timezone} for dates, reminders, and scheduled actions unless the user says otherwise."
        )
    return prompt


def put_provider(
    providers: dict[str, dict[str, str]],
    name: str,
    *,
    api_key: str = "",
    api_base: str = "",
) -> None:
    data = {}
    if api_key:
        data["apiKey"] = api_key
    if api_base:
        data["apiBase"] = api_base
    if data:
        providers[name] = data


providers: dict[str, dict[str, str]] = {}
put_provider(providers, "openrouter", api_key=secret_env("OPENROUTER_API_KEY"))
put_provider(providers, "openai", api_key=secret_env("OPENAI_API_KEY"))
put_provider(providers, "anthropic", api_key=secret_env("ANTHROPIC_API_KEY"))
put_provider(providers, "vllm", api_key=secret_env("VLLM_API_KEY"), api_base=env("VLLM_API_BASE"))

cfg: dict = {
    "agents": {
        "defaults": {
            "provider": env("DEFAULT_PROVIDER", "openrouter"),
            "model": os.environ["DEFAULT_MODEL"],
            "workspace": str(workspace),
            "systemPrompt": system_prompt(),
        }
    },
    "channels": {},
    "gateway": {
        "port": int(env("NANOBOT_GATEWAY_PORT", "18790")),
    },
}

if providers:
    cfg["providers"] = providers

allow_from = csv_list("CHANNEL_ALLOW_FROM")
group_allow_from = csv_list("CHANNEL_GROUP_ALLOW_FROM")
group_policy = env("CHANNEL_GROUP_POLICY", "mention")


def require_allow_from(channel: str) -> None:
    if not allow_from:
        raise SystemExit(f"CHANNEL_ALLOW_FROM is required when {channel} is enabled")


if env("TELEGRAM_ENABLED", "false").lower() == "true":
    token = secret_env("TELEGRAM_TOKEN")
    if token:
        require_allow_from("telegram")
        cfg["channels"]["telegram"] = {
            "enabled": True,
            "token": token,
            "allowFrom": allow_from,
            "groupPolicy": group_policy,
            "groupAllowFrom": group_allow_from,
        }

if env("SLACK_ENABLED", "false").lower() == "true":
    bot_token = secret_env("SLACK_BOT_TOKEN")
    app_token = secret_env("SLACK_APP_TOKEN")
    if bot_token and app_token:
        require_allow_from("slack")
        cfg["channels"]["slack"] = {
            "enabled": True,
            "botToken": bot_token,
            "appToken": app_token,
            "allowFrom": allow_from,
            "groupPolicy": group_policy,
            "groupAllowFrom": group_allow_from,
        }

if env("FEISHU_ENABLED", "false").lower() == "true":
    app_id = env("FEISHU_APP_ID")
    app_secret = secret_env("FEISHU_APP_SECRET")
    if app_id and app_secret:
        require_allow_from("feishu")
        cfg["channels"]["feishu"] = {
            "enabled": True,
            "appId": app_id,
            "appSecret": app_secret,
            "allowFrom": allow_from,
            "groupPolicy": group_policy,
            "groupAllowFrom": group_allow_from,
        }

with open(config_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, ensure_ascii=False, indent=2)

print(f"Wrote config to {config_path}")
