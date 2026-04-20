from __future__ import annotations

import argparse
import tarfile
import unittest

from installer import install


class InstallerTest(unittest.TestCase):
    def test_package_contains_runtime_app_files(self) -> None:
        package = install.package_app()
        try:
            with tarfile.open(package, "r:gz") as archive:
                names = set(archive.getnames())
        finally:
            package.unlink(missing_ok=True)

        self.assertIn("console/api.py", names)
        self.assertIn("console/static/index.html", names)
        self.assertIn("docker/entrypoint.sh", names)
        self.assertIn("docker/sitecustomize.py", names)
        self.assertIn("Dockerfile", names)
        self.assertIn("docs/PROJECT_SUMMARY.md", names)

    def test_missing_prereqs_includes_compose_and_network(self) -> None:
        missing = install.missing_prereqs(
            {
                "docker": "ok",
                "compose": "missing",
                "network": "unknown",
            }
        )

        self.assertEqual(missing, ["Docker Compose", "outbound network"])

    def test_bootstrap_runs_with_bash(self) -> None:
        args = argparse.Namespace(remote_root="/opt/test root", console_port="8787")
        captured: dict[str, str | None] = {}

        def fake_run_ssh(args, command: str, *, input_text: str | None = None):
            captured["command"] = command
            captured["input_text"] = input_text
            return None

        original = install.run_ssh
        try:
            install.run_ssh = fake_run_ssh
            install.run_bootstrap(args, "probe")
        finally:
            install.run_ssh = original

        self.assertIn("bash -s -- probe", str(captured["command"]))
        self.assertIn("/opt/test root", str(captured["command"]))
        self.assertIn("probe()", str(captured["input_text"]))
        self.assertNotIn("\r\n", str(captured["input_text"]))


if __name__ == "__main__":
    unittest.main()
