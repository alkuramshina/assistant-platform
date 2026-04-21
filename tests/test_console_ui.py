from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from console.api import ConsoleAPI


class ConsoleUITest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.server = ConsoleAPI(("127.0.0.1", 0), Path(self.tmp.name) / "console.db")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        try:
            self.tmp.cleanup()
        except PermissionError:
            pass

    def read(self, path: str) -> tuple[str, str]:
        with urllib.request.urlopen(f"{self.base}{path}", timeout=5) as response:
            body = response.read().decode("utf-8")
            return response.headers["Content-Type"], body

    def test_index_serves_working_console(self) -> None:
        content_type, body = self.read("/")

        self.assertIn("text/html", content_type)
        self.assertIn("Create bot", body)
        self.assertIn("Start", body)
        self.assertIn("Stop", body)
        self.assertIn("Activity", body)
        self.assertIn("Runtime logs", body)
        self.assertIn("scoped to the selected bot", body)
        self.assertIn('role="tablist"', body)
        self.assertIn('data-tab="activity"', body)
        self.assertIn('data-tab="runtime"', body)
        self.assertIn('data-tab-panel="runtime"', body)
        self.assertIn("secret file", body)
        self.assertIn("Telegram token", body)
        self.assertIn("Proxy URL", body)
        self.assertIn("Timezone", body)
        self.assertIn("Europe/Moscow", body)
        self.assertIn("OpenRouter API key", body)
        self.assertIn("OLCALL markers", body)
        self.assertIn('id="provider-model"', body)
        self.assertIn("protect it with HTTPS and a login", body)
        self.assertIn("<legend>Bot</legend>", body)
        self.assertIn("<legend>Telegram</legend>", body)
        self.assertIn("<legend>Model</legend>", body)
        self.assertIn("Bot details", body)
        self.assertIn("Keep this console private.", body)
        self.assertIn("/static/app.js", body)
        self.assertNotIn("Local prototype", body)
        self.assertNotIn("Bind this console locally", body)
        self.assertNotIn("Select a bot", body)
        self.assertNotIn("Existing Telegram token secret file", body)
        self.assertNotIn("Existing provider API key secret file", body)

    def test_static_assets_include_api_wiring(self) -> None:
        content_type, body = self.read("/static/app.js")

        self.assertTrue("javascript" in content_type)
        self.assertIn("/api/bots", body)
        self.assertIn("/logs", body)
        self.assertIn("limit=100", body)
        self.assertIn("/runtime-logs", body)
        self.assertIn("/start", body)
        self.assertIn("/stop", body)
        self.assertIn('cache: "no-store"', body)
        self.assertIn("withCacheBust", body)
        self.assertIn("refreshSelected", body)
        self.assertIn("switchLogTab", body)
        self.assertIn("modelPresets", body)
        self.assertIn("Llama 3.3 70B Instruct (free)", body)
        self.assertLess(body.index("meta-llama/llama-3.3-70b-instruct:free"), body.index("openrouter/free"))
        self.assertIn("openrouter/free", body)
        self.assertIn("<dt>Provider</dt><dd>OpenRouter</dd>", body)
        self.assertNotIn("localStorage", body)
        self.assertNotIn("sessionStorage", body)

    def test_static_css_is_served(self) -> None:
        content_type, body = self.read("/static/styles.css")

        self.assertIn("text/css", content_type)
        self.assertIn(".grid", body)
        self.assertIn("grid-column: 1 / -1", body)
        self.assertIn(".tabs", body)
        self.assertIn(".tab-panel[hidden]", body)
        self.assertIn(".log-list", body)
        self.assertIn(".section-note", body)
        self.assertIn("font-family: Consolas", body)
        self.assertIn("background: #171914", body)
        self.assertIn("height: 360px", body)
        self.assertIn("height: 320px", body)
        self.assertNotIn("max-height: 420px", body)
        self.assertIn("border-radius: 8px", body)

    def test_static_path_traversal_is_not_served(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.read("/static/../api.py")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
