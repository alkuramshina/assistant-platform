from __future__ import annotations

import unittest

from console.redact import redact_secrets


class RedactTest(unittest.TestCase):
    def test_redacts_telegram_bot_tokens(self) -> None:
        text = "token=1234567890:AAGabcdefghijklmnopqrstuvwxyz012345678"

        redacted = redact_secrets(text)

        self.assertEqual(redacted, "token=<redacted>")

    def test_redacts_openrouter_keys(self) -> None:
        text = "provider sk-or-v1-abcdefghijklmnopqrstuvwxyz0123456789"

        redacted = redact_secrets(text)

        self.assertEqual(redacted, "provider <redacted>")


if __name__ == "__main__":
    unittest.main()
