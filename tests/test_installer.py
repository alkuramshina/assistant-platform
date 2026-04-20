from __future__ import annotations

import argparse
import subprocess
import tarfile
import unittest

from installer import install


class InstallerTest(unittest.TestCase):
    def test_run_sends_input_text_as_bytes(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(cmd, **kwargs):
            captured.update(kwargs)
            return subprocess.CompletedProcess(cmd, 0, b"ok\n", b"")

        original = install.subprocess.run
        try:
            install.subprocess.run = fake_run
            result = install.run(["ssh", "example"], input_text="set -eu\n")
        finally:
            install.subprocess.run = original

        self.assertEqual(captured["input"], b"set -eu\n")
        self.assertNotIn("text", captured)
        self.assertEqual(result.stdout, "ok\n")

    def test_ssh_base_has_non_interactive_timeout_options(self) -> None:
        args = argparse.Namespace(port="22", identity_file=None, target="user@example.com")
        command = install.ssh_base(args)

        self.assertIn("BatchMode=yes", command)
        self.assertIn("ConnectTimeout=10", command)
        self.assertIn("ConnectionAttempts=1", command)
        self.assertIn("NumberOfPasswordPrompts=0", command)
        self.assertIn("StrictHostKeyChecking=accept-new", command)

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
                "sudo": "ok",
                "docker": "ok",
                "compose": "missing",
                "network": "unknown",
            }
        )

        self.assertEqual(missing, ["Docker Compose", "outbound network"])

    def test_missing_prereqs_includes_passwordless_sudo(self) -> None:
        missing = install.missing_prereqs(
            {
                "sudo": "password_required",
                "docker": "ok",
                "compose": "ok",
                "network": "ok",
            }
        )

        self.assertEqual(missing, ["passwordless sudo"])

    def test_sudo_setup_commands_use_target_user(self) -> None:
        args = argparse.Namespace(target="ssh_user@ssh_ip_addr")

        commands = install.sudo_setup_commands(args)

        self.assertIn("ssh_user ALL=(ALL) NOPASSWD:ALL", commands[0])
        self.assertIn("/etc/sudoers.d/nanobot-console-ssh_user", commands[0])
        self.assertEqual(commands[-1], "sudo -n true")

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
