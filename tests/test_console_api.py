from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from console.api import ConsoleAPI


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[list[str]] = []

    def run(self, command: list[str], *, cwd: Path | None = None) -> None:
        self.commands.append(command)


class APITest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmp.name) / "console.db"
        self.bot_root = Path(self.tmp.name) / "bots"
        self.secret_root = Path(self.tmp.name) / "secrets"
        self.channel_secret = Path(self.tmp.name) / "channel"
        self.provider_secret = Path(self.tmp.name) / "provider"
        self.channel_secret.write_text("super-secret-channel", encoding="utf-8")
        self.provider_secret.write_text("super-secret-provider", encoding="utf-8")
        self.runner = FakeRunner()
        self.server = ConsoleAPI(("127.0.0.1", 0), self.db_path, self.bot_root, self.secret_root, self.runner)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

    def get(self, path: str) -> dict:
        with urllib.request.urlopen(f"{self.base}{path}", timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))

    def post(self, path: str, payload: dict) -> tuple[int, dict]:
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, json.loads(response.read().decode("utf-8"))

    def test_health(self) -> None:
        self.assertEqual(self.get("/health"), {"ok": True})

    def test_bot_lifecycle_and_secret_refs(self) -> None:
        status, created = self.post(
            "/api/bots",
            {
                "name": "sales",
                "allowed_user_ids": "123",
                "provider_base_url": "https://provider.example/v1",
                "provider_model": "free-model",
                "system_prompt": "Be concise",
                "channel_secret_ref": str(self.channel_secret),
                "provider_secret_ref": str(self.provider_secret),
            },
        )
        self.assertEqual(status, 201)
        bot = created["bot"]
        self.assertEqual(bot["name"], "sales")
        self.assertEqual(bot["status"], "stopped")
        self.assertNotIn("super-secret", json.dumps(bot).lower())

        listed = self.get("/api/bots")["bots"]
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], bot["id"])

        fetched = self.get(f"/api/bots/{bot['id']}")["bot"]
        self.assertEqual(fetched["id"], bot["id"])

        _, started = self.post(f"/api/bots/{bot['id']}/start", {})
        self.assertEqual(started["bot"]["status"], "running")
        self.assertIn("up", self.runner.commands[-1])
        self.assertTrue((self.bot_root / bot["id"] / "docker-compose.yml").is_file())

        _, stopped = self.post(f"/api/bots/{bot['id']}/stop", {})
        self.assertEqual(stopped["bot"]["status"], "stopped")
        self.assertIn("down", self.runner.commands[-1])

    def test_activity_logs_persist(self) -> None:
        _, created = self.post("/api/bots", {"name": "support"})
        bot_id = created["bot"]["id"]
        status, logged = self.post(
            f"/api/bots/{bot_id}/logs",
            {
                "telegram_user_id": "123",
                "user_request": "hello",
                "assistant_response": "hi",
                "provider": "openrouter",
                "model": "free",
                "status": "ok",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(logged["log"]["bot_id"], bot_id)

        logs = self.get(f"/api/bots/{bot_id}/logs")["logs"]
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["user_request"], "hello")

        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

        self.server = ConsoleAPI(("127.0.0.1", 0), self.db_path, self.bot_root, self.secret_root, self.runner)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

        persisted = self.get(f"/api/bots/{bot_id}/logs")["logs"]
        self.assertEqual(len(persisted), 1)

    def test_missing_bot_404(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/api/bots/missing")
        self.assertEqual(cm.exception.code, 404)

    def test_secret_values_are_written_as_refs_only(self) -> None:
        status, created = self.post(
            "/api/bots",
            {
                "name": "smoke",
                "allowed_user_ids": "123",
                "channel_secret_value": "telegram-secret",
                "provider_secret_value": "provider-secret",
            },
        )

        self.assertEqual(status, 201)
        serialized = json.dumps(created)
        self.assertNotIn("telegram-secret", serialized)
        self.assertNotIn("provider-secret", serialized)
        bot = created["bot"]
        channel_ref = Path(bot["channel_secret_ref"])
        provider_ref = Path(bot["provider_secret_ref"])
        self.assertTrue(channel_ref.is_file())
        self.assertTrue(provider_ref.is_file())
        self.assertEqual(channel_ref.read_text(encoding="utf-8"), "telegram-secret")
        self.assertEqual(provider_ref.read_text(encoding="utf-8"), "provider-secret")
        self.assertTrue(channel_ref.is_relative_to(self.secret_root))


if __name__ == "__main__":
    unittest.main()
