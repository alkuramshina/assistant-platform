from __future__ import annotations

import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

from console.api import ConsoleAPI


class ConsoleAPIHeadersTest(unittest.TestCase):
    def test_json_api_responses_are_not_cached(self) -> None:
        tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        server = ConsoleAPI(("127.0.0.1", 0), Path(tmp.name) / "console.db")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            host, port = server.server_address
            with urllib.request.urlopen(f"http://{host}:{port}/health", timeout=5) as response:
                self.assertEqual(response.headers["Cache-Control"], "no-store")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
            try:
                tmp.cleanup()
            except PermissionError:
                pass


if __name__ == "__main__":
    unittest.main()
