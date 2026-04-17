from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from console.deploy import DeploymentEngine, DeploymentError


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[list[str], Path | None]] = []

    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        self.commands.append((command, cwd))


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
    def test_deploy_renders_isolated_compose(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
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
            self.assertNotIn("docker" + ".sock", compose)
            self.assertTrue((tmp / "bots" / bot["id"] / "data").is_dir())
            self.assertTrue((tmp / "bots" / bot["id"] / "workspace").is_dir())
            self.assertTrue((tmp / "bots" / bot["id"] / "secrets" / "channel").is_file())
            self.assertEqual(runner.commands[0][0][:4], ["docker", "compose", "-p", "nanobot_bot_abc"])

    def test_two_bots_do_not_share_paths_or_projects(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            engine = DeploymentEngine(tmp / "bots", FakeRunner())
            first = engine.deploy(bot_record(tmp, "bot-one"))
            second = engine.deploy(bot_record(tmp, "bot-two"))

            self.assertNotEqual(first.root, second.root)
            self.assertNotEqual(engine.project_name("bot-one"), engine.project_name("bot-two"))

    def test_missing_allowlist_fails_before_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            runner = FakeRunner()
            engine = DeploymentEngine(tmp / "bots", runner)
            bot = bot_record(tmp)
            bot["allowed_user_ids"] = ""

            with self.assertRaises(DeploymentError):
                engine.start(bot)
            self.assertEqual(runner.commands, [])

    def test_missing_secret_ref_fails_before_runner(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            runner = FakeRunner()
            engine = DeploymentEngine(tmp / "bots", runner)
            bot = bot_record(tmp)
            bot["provider_secret_ref"] = ""

            with self.assertRaises(DeploymentError):
                engine.start(bot)
            self.assertEqual(runner.commands, [])


if __name__ == "__main__":
    unittest.main()
