import json
import os
from pathlib import Path


home = Path(os.environ.get("NANOBOT_HOME", "/home/app/.nanobot"))
config_path = Path(os.environ.get("NANOBOT_CONFIG", home / "config.json"))
workspace = Path(os.environ.get("NANOBOT_WORKSPACE", "/workspace"))

home.mkdir(parents=True, exist_ok=True)
config_path.parent.mkdir(parents=True, exist_ok=True)
workspace.mkdir(parents=True, exist_ok=True)


def csv_list(name: str) -> list[str]:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return []
    return [value.strip() for value in raw.split(",") if value.strip()]


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


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
put_provider(providers, "openrouter", api_key=env("OPENROUTER_API_KEY"))
put_provider(providers, "openai", api_key=env("OPENAI_API_KEY"))
put_provider(providers, "anthropic", api_key=env("ANTHROPIC_API_KEY"))
put_provider(providers, "vllm", api_key=env("VLLM_API_KEY"), api_base=env("VLLM_API_BASE"))

cfg: dict = {
    "agents": {
        "defaults": {
            "provider": env("DEFAULT_PROVIDER", "openrouter"),
            "model": os.environ["DEFAULT_MODEL"],
            "workspace": str(workspace),
            "systemPrompt": env(
                "SYSTEM_PROMPT",
                "You are a concise and reliable work assistant.",
            ),
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

if env("TELEGRAM_ENABLED", "false").lower() == "true":
    token = env("TELEGRAM_TOKEN")
    if token:
        cfg["channels"]["telegram"] = {
            "enabled": True,
            "token": token,
            "allowFrom": allow_from,
            "groupPolicy": group_policy,
            "groupAllowFrom": group_allow_from,
        }

if env("SLACK_ENABLED", "false").lower() == "true":
    bot_token = env("SLACK_BOT_TOKEN")
    app_token = env("SLACK_APP_TOKEN")
    if bot_token and app_token:
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
    app_secret = env("FEISHU_APP_SECRET")
    if app_id and app_secret:
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
