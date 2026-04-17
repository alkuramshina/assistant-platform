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
        self.tmp = tempfile.TemporaryDirectory()
        self.server = ConsoleAPI(("127.0.0.1", 0), Path(self.tmp.name) / "console.db")
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base = f"http://{host}:{port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)
        self.tmp.cleanup()

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
        self.assertIn("secret file", body)
        self.assertIn("/static/app.js", body)

    def test_static_assets_include_api_wiring(self) -> None:
        content_type, body = self.read("/static/app.js")

        self.assertTrue("javascript" in content_type)
        self.assertIn("/api/bots", body)
        self.assertIn("/logs", body)
        self.assertIn("/start", body)
        self.assertIn("/stop", body)
        self.assertNotIn("localStorage", body)

    def test_static_css_is_served(self) -> None:
        content_type, body = self.read("/static/styles.css")

        self.assertIn("text/css", content_type)
        self.assertIn(".grid", body)
        self.assertIn("border-radius: 8px", body)

    def test_static_path_traversal_is_not_served(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.read("/static/../api.py")
        self.assertEqual(cm.exception.code, 404)


if __name__ == "__main__":
    unittest.main()
