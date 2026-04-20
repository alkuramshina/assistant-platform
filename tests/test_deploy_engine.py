from __future__ import annotations

import subprocess
import unittest
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

from console.deploy import CommandRunner, DeploymentEngine, DeploymentError


@contextmanager
def workspace_temp_dir():
    root = Path(".test-tmp")
    root.mkdir(exist_ok=True)
    tmp = root / uuid4().hex
    tmp.mkdir(parents=True, exist_ok=False)
    yield tmp


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[list[str], Path | None]] = []
        self.captured = "logs\n"

    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        self.commands.append((command, cwd))

    def capture(self, command: list[str], *, cwd: Path | None = None) -> str:
        self.commands.append((command, cwd))
        return self.captured


def bot_record(tmp: Path, bot_id: str = "bot-abc") -> dict:
    channel = tmp / f"{bot_id}-channel"
    provider = tmp / f"{bot_id}-provider"
    channel.write_text("channel-secret", encoding="utf-8")
    provider.write_text("provider-secret", encoding="utf-8")
    return {
        "id": bot_id,
        "name": "Bot",
        "allowed_user_ids": "123",
        "provider_base_url": "https://provider.example/v1",
        "provider_model": "free-model",
        "system_prompt": "Be concise",
        "channel_secret_ref": str(channel),
        "provider_secret_ref": str(provider),
    }


class DeploymentEngineTest(unittest.TestCase):
    def test_command_runner_surfaces_compose_output(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(command, **kwargs):
            captured.update(kwargs)
            return subprocess.CompletedProcess(command, 1, "out text\n", "err text\n")

        original = subprocess.run
        try:
            subprocess.run = fake_run
            with self.assertRaises(DeploymentError) as cm:
                CommandRunner().run(["docker", "compose", "up"], cwd=Path("/tmp/bot"))
        finally:
            subprocess.run = original

        self.assertTrue(captured["text"])
        self.assertEqual(captured["stdout"], subprocess.PIPE)
        self.assertIn("exit code 1", str(cm.exception))
        self.assertIn("out text", str(cm.exception))
        self.assertIn("err text", str(cm.exception))

    def test_deploy_renders_isolated_compose(self) -> None:
        with workspace_temp_dir() as tmp:
            runner = FakeRunner()
            engine = DeploymentEngine(tmp / "bots", runner)
            bot = bot_record(tmp)

            result = engine.start(bot)
            compose_path = Path(result["compose"])
            compose = compose_path.read_text(encoding="utf-8")

            self.assertIn("nanobot:", compose)
            self.assertIn("/data", compose)
            self.assertIn("/workspace", compose)
            self.assertIn("channel_secret", compose)
            self.assertIn("NANOBOT_CONSOLE_ACTIVITY_URL", compose)
            self.assertIn("host.docker.internal:host-gateway", compose)
            self.assertIn("DEFAULT_PROVIDER: vllm", compose)
            self.assertIn("VLLM_API_KEY_FILE: /run/secrets/provider_secret", compose)
            self.assertNotIn("docker" + ".sock", compose)
            self.assertTrue((tmp / "bots" / bot["id"] / "data").is_dir())
            self.assertTrue((tmp / "bots" / bot["id"] / "workspace").is_dir())
            self.assertTrue((tmp / "bots" / bot["id"] / "secrets" / "channel").is_file())
            self.assertEqual(runner.commands[0][0][:4], ["docker", "compose", "-p", "nanobot_bot_abc"])

    def test_render_compose_escapes_yaml_sensitive_values(self) -> None:
        with workspace_temp_dir() as tmp:
            engine = DeploymentEngine(tmp / "bots", FakeRunner())
            bot = bot_record(tmp)
            bot["provider_model"] = "nvidia/nemotron-3-super-120b-a12b:free"
            bot["provider_base_url"] = "https://openrouter.ai/api/v1"
            bot["system_prompt"] = "Line one:\n- keep this as text\nLine three"

            paths = engine.deploy(bot)
            compose = paths.compose.read_text(encoding="utf-8")

            self.assertIn('DEFAULT_MODEL: "nvidia/nemotron-3-super-120b-a12b:free"', compose)
            self.assertIn('SYSTEM_PROMPT: "Line one:\\n- keep this as text\\nLine three"', compose)
            self.assertIn(f'- "{paths.data.resolve().as_posix()}:/home/app/.nanobot"', compose)
            self.assertNotIn("\n- keep this as text", compose)

    def test_two_bots_do_not_share_paths_or_projects(self) -> None:
        with workspace_temp_dir() as tmp:
            engine = DeploymentEngine(tmp / "bots", FakeRunner())
            first = engine.deploy(bot_record(tmp, "bot-one"))
            second = engine.deploy(bot_record(tmp, "bot-two"))

            self.assertNotEqual(first.root, second.root)
            self.assertNotEqual(engine.project_name("bot-one"), engine.project_name("bot-two"))

    def test_runtime_logs_reads_compose_logs_for_bot(self) -> None:
        with workspace_temp_dir() as tmp:
            runner = FakeRunner()
            engine = DeploymentEngine(tmp / "bots", runner)
            bot = bot_record(tmp)
            engine.deploy(bot)

            logs = engine.runtime_logs(bot["id"])

            self.assertEqual(logs, "logs\n")
            command, cwd = runner.commands[-1]
            self.assertEqual(command[:4], ["docker", "compose", "-p", "nanobot_bot_abc"])
            self.assertIn("logs", command)
            self.assertEqual(cwd, tmp / "bots" / bot["id"])

    def test_missing_allowlist_fails_before_runner(self) -> None:
        with workspace_temp_dir() as tmp:
            runner = FakeRunner()
            engine = DeploymentEngine(tmp / "bots", runner)
            bot = bot_record(tmp)
            bot["allowed_user_ids"] = ""

            with self.assertRaises(DeploymentError):
                engine.start(bot)
            self.assertEqual(runner.commands, [])

    def test_missing_secret_ref_fails_before_runner(self) -> None:
        with workspace_temp_dir() as tmp:
            runner = FakeRunner()
            engine = DeploymentEngine(tmp / "bots", runner)
            bot = bot_record(tmp)
            bot["provider_secret_ref"] = ""

            with self.assertRaises(DeploymentError):
                engine.start(bot)
            self.assertEqual(runner.commands, [])


if __name__ == "__main__":
    unittest.main()
