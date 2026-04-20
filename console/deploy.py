"""Per-bot Compose rendering and deployment primitives."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class Runner(Protocol):
    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        ...

    def capture(self, command: list[str], *, cwd: Path | None = None) -> str:
        ...


class CommandRunner:
    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        self.capture(command, cwd=cwd)

    def capture(self, command: list[str], *, cwd: Path | None = None) -> str:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            details = "\n".join(
                part
                for part in (
                    f"Command failed with exit code {result.returncode}: {format_command(command)}",
                    f"stdout:\n{result.stdout.strip()}" if result.stdout.strip() else "",
                    f"stderr:\n{result.stderr.strip()}" if result.stderr.strip() else "",
                )
                if part
            )
            raise DeploymentError(details)
        return result.stdout


class DeploymentError(ValueError):
    pass


def format_command(command: list[str]) -> str:
    return " ".join(subprocess.list2cmdline([part]) for part in command)


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

    def runtime_logs(self, bot_id: str, tail: int = 200) -> str:
        paths = self.paths(bot_id)
        if not paths.compose.is_file():
            raise DeploymentError(f"Compose file not found for bot: {bot_id}")
        project = self.project_name(bot_id)
        safe_tail = max(20, min(int(tail), 1000))
        return self.runner.capture(
            [
                "docker",
                "compose",
                "-p",
                project,
                "-f",
                str(paths.compose),
                "logs",
                "--timestamps",
                "--tail",
                str(safe_tail),
            ],
            cwd=paths.root,
        )

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
        data_volume = self._yaml_string(f"{data}:/home/app/.nanobot")
        workspace_volume = self._yaml_string(f"{workspace}:/workspace")
        model = self._yaml_string(str(bot.get("provider_model", "")))
        base_url = self._yaml_string(str(bot.get("provider_base_url", "")))
        prompt = self._yaml_string(str(bot.get("system_prompt", "")))
        allow = self._yaml_string(str(bot.get("allowed_user_ids", "")))

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
      DEFAULT_PROVIDER: vllm
      DEFAULT_MODEL: {model}
      SYSTEM_PROMPT: {prompt}
      VLLM_API_BASE: {base_url}
      VLLM_API_KEY_FILE: /run/secrets/provider_secret
      TELEGRAM_TOKEN_FILE: /run/secrets/channel_secret
      CHANNEL_TYPE: telegram
      CHANNEL_ALLOW_FROM: {allow}
      TELEGRAM_ENABLED: "true"
      NANOBOT_CONSOLE_BOT_ID: {self._yaml_string(str(bot.get("id", "")))}
      NANOBOT_CONSOLE_ACTIVITY_URL: {self._yaml_string(str(bot.get("activity_url", "")))}
    volumes:
      - {data_volume}
      - {workspace_volume}
    extra_hosts:
      - "host.docker.internal:host-gateway"
    secrets:
      - source: provider_secret
        target: provider_secret
        uid: "1000"
        gid: "1000"
        mode: 0440
      - source: channel_secret
        target: channel_secret
        uid: "1000"
        gid: "1000"
        mode: 0440
    command: ["/app/entrypoint.sh"]

secrets:
  provider_secret:
    file: {self._yaml_string(provider_secret)}
  channel_secret:
    file: {self._yaml_string(channel_secret)}
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
        return str(path.resolve()).replace("\\", "/")

    def _yaml_string(self, value: str) -> str:
        return json.dumps(value)
