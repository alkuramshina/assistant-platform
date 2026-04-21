from __future__ import annotations

import unittest
from pathlib import Path


class RuntimeImageTest(unittest.TestCase):
    def test_entrypoint_exposes_app_pythonpath_for_sitecustomize_hook(self) -> None:
        entrypoint = Path("docker/entrypoint.sh").read_text(encoding="utf-8")

        self.assertIn('PYTHONPATH="/app', entrypoint)
        self.assertIn("nanobot gateway", entrypoint)

    def test_activity_hook_logs_activation_and_post_failures(self) -> None:
        hook = Path("docker/sitecustomize.py").read_text(encoding="utf-8")

        self.assertIn("console activity hook enabled", hook)
        self.assertIn("console activity hook post failed", hook)
        self.assertIn("<redacted>", hook)

    def test_generated_config_has_plain_text_guardrails(self) -> None:
        generator = Path("docker/generate_config.py").read_text(encoding="utf-8")

        self.assertIn("DEFAULT_SYSTEM_PROMPT", generator)
        self.assertIn("OLCALL markers", generator)
        self.assertIn("JSON tool calls", generator)
        self.assertIn("ask one brief clarifying question", generator)
        self.assertIn("NANOBOT_TIMEZONE", generator)


if __name__ == "__main__":
    unittest.main()
