"""Per-bot Compose rendering and deployment primitives."""

from __future__ import annotations

import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class Runner(Protocol):
    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        ...


class CommandRunner:
    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        subprocess.run(command, cwd=cwd, check=True)


class DeploymentError(ValueError):
    pass


@dataclass(frozen=True)
class BotPaths:
    root: Path
    data: Path
    workspace: Path
    secrets: Path
    compose: Path
    channel_secret: Path
    provider_secret: Path


class DeploymentEngine:
    def __init__(self, bot_root: str | Path, runner: Runner | None = None):
        self.bot_root = Path(bot_root)
        self.runner = runner or CommandRunner()

    def start(self, bot: dict[str, Any]) -> dict[str, Any]:
        paths = self.deploy(bot)
        project = self.project_name(bot["id"])
        self.runner.run(
            ["docker", "compose", "-p", project, "-f", str(paths.compose), "up", "-d"],
            cwd=paths.root,
        )
        return {"status": "running", "project": project, "compose": str(paths.compose)}

    def stop(self, bot: dict[str, Any]) -> dict[str, Any]:
        paths = self.paths(bot["id"])
        project = self.project_name(bot["id"])
        self.runner.run(
            ["docker", "compose", "-p", project, "-f", str(paths.compose), "down"],
            cwd=paths.root,
        )
        return {"status": "stopped", "project": project, "compose": str(paths.compose)}

    def deploy(self, bot: dict[str, Any]) -> BotPaths:
        self.validate(bot)
        paths = self.paths(bot["id"])
        for path in (paths.data, paths.workspace, paths.secrets):
            path.mkdir(parents=True, exist_ok=True)
        self._copy_secret(bot["channel_secret_ref"], paths.channel_secret)
        self._copy_secret(bot["provider_secret_ref"], paths.provider_secret)
        paths.compose.write_text(self.render_compose(bot, paths), encoding="utf-8")
        return paths

    def paths(self, bot_id: str) -> BotPaths:
        safe_id = self.safe_id(bot_id)
        root = self.bot_root / safe_id
        return BotPaths(
            root=root,
            data=root / "data",
            workspace=root / "workspace",
            secrets=root / "secrets",
            compose=root / "docker-compose.yml",
            channel_secret=root / "secrets" / "channel",
            provider_secret=root / "secrets" / "provider",
        )

    def validate(self, bot: dict[str, Any]) -> None:
        if not str(bot.get("allowed_user_ids", "")).strip():
            raise DeploymentError("allowed_user_ids is required before deploy")
        for field in ("channel_secret_ref", "provider_secret_ref"):
            ref = str(bot.get(field, "")).strip()
            if not ref:
                raise DeploymentError(f"{field} is required before deploy")
            if not Path(ref).is_file():
                raise DeploymentError(f"{field} must point to an existing file")

    def render_compose(self, bot: dict[str, Any], paths: BotPaths) -> str:
        data = self._compose_path(paths.data)
        workspace = self._compose_path(paths.workspace)
        channel_secret = self._compose_path(paths.channel_secret)
        provider_secret = self._compose_path(paths.provider_secret)
        model = self._quote(str(bot.get("provider_model", "")))
        base_url = self._quote(str(bot.get("provider_base_url", "")))
        prompt = self._quote(str(bot.get("system_prompt", "")))
        allow = self._quote(str(bot.get("allowed_user_ids", "")))

        return f"""services:
  nanobot:
    image: ${{NANOBOT_IMAGE:-nanobot-enterprise-pilot:dev}}
    restart: unless-stopped
    init: true
    user: "${{APP_UID:-1000}}:${{APP_GID:-1000}}"
    working_dir: /workspace
    environment:
      NANOBOT_HOME: /home/app/.nanobot
      NANOBOT_CONFIG: /home/app/.nanobot/config.json
      NANOBOT_WORKSPACE: /workspace
      DEFAULT_PROVIDER: openrouter
      DEFAULT_MODEL: {model}
      SYSTEM_PROMPT: {prompt}
      VLLM_API_BASE: {base_url}
      OPENROUTER_API_KEY_FILE: /run/secrets/provider_secret
      TELEGRAM_TOKEN_FILE: /run/secrets/channel_secret
      CHANNEL_TYPE: telegram
      CHANNEL_ALLOW_FROM: {allow}
      TELEGRAM_ENABLED: "true"
      NANOBOT_CONSOLE_BOT_ID: {self._quote(str(bot.get("id", "")))}
      NANOBOT_CONSOLE_ACTIVITY_URL: {self._quote(str(bot.get("activity_url", "")))}
    volumes:
      - {data}:/home/app/.nanobot
      - {workspace}:/workspace
    extra_hosts:
      - "host.docker.internal:host-gateway"
    secrets:
      - provider_secret
      - channel_secret
    command: ["/app/entrypoint.sh"]

secrets:
  provider_secret:
    file: {provider_secret}
  channel_secret:
    file: {channel_secret}
"""

    def project_name(self, bot_id: str) -> str:
        return f"nanobot_{self.safe_id(bot_id).replace('-', '_')}"

    def safe_id(self, value: str) -> str:
        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", value).strip("-")
        if not safe:
            raise DeploymentError("bot id is invalid")
        return safe[:64]

    def _copy_secret(self, source: str, dest: Path) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        dest.chmod(0o600)

    def _compose_path(self, path: Path) -> str:
        return self._quote(str(path.resolve()).replace("\\", "/"))

    def _quote(self, value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
