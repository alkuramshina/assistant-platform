from __future__ import annotations

import argparse
import json
import subprocess
import tarfile
import unittest
from pathlib import Path
from uuid import uuid4

from deployer import deploy


class DeployerTest(unittest.TestCase):
    def test_version_does_not_expose_phase_marker(self) -> None:
        self.assertNotIn("phase", deploy.VERSION.lower())
        self.assertNotIn("prototype", deploy.VERSION.lower())

    def test_bootstrap_has_compose_package_fallbacks(self) -> None:
        script = deploy.REMOTE_BOOTSTRAP.read_text(encoding="utf-8")

        self.assertIn("docker-compose-plugin", script)
        self.assertIn("docker-compose-v2", script)
        self.assertIn("docker-compose", script)
        self.assertIn("compose_install_failed", script)

    def test_bootstrap_finalization_prints_progress_markers(self) -> None:
        script = deploy.REMOTE_BOOTSTRAP.read_text(encoding="utf-8")

        self.assertIn("docker_daemon=check", script)
        self.assertIn("docker_build=start", script)
        self.assertIn("docker_build=ok", script)
        self.assertIn("service_restart=start", script)

    def test_control_script_has_service_commands(self) -> None:
        script = deploy.REMOTE_CONTROL.read_text(encoding="utf-8")

        self.assertIn("restart|status|logs|bot-logs|url", script)
        self.assertIn("systemctl restart", script)
        self.assertIn("journalctl -u", script)
        self.assertIn("docker compose -p", script)
        self.assertIn("--timestamps", script)
        self.assertIn("nanobot-console", script)

    def test_run_sends_input_text_as_bytes(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(cmd, **kwargs):
            captured.update(kwargs)
            return subprocess.CompletedProcess(cmd, 0, b"ok\n", b"")

        original = deploy.subprocess.run
        try:
            deploy.subprocess.run = fake_run
            result = deploy.run(["ssh", "example"], input_text="set -eu\n")
        finally:
            deploy.subprocess.run = original

        self.assertEqual(captured["input"], b"set -eu\n")
        self.assertNotIn("text", captured)
        self.assertEqual(result.stdout, "ok\n")

    def test_run_stream_leaves_output_uncaptured_and_sends_input_as_bytes(self) -> None:
        captured: dict[str, object] = {}

        def fake_run(cmd, **kwargs):
            captured.update(kwargs)
            return subprocess.CompletedProcess(cmd, 0, None, None)

        original = deploy.subprocess.run
        try:
            deploy.subprocess.run = fake_run
            deploy.run_stream(["ssh", "example"], input_text="password\n")
        finally:
            deploy.subprocess.run = original

        self.assertEqual(captured["input"], b"password\n")
        self.assertTrue(captured["check"])
        self.assertNotIn("stdout", captured)
        self.assertNotIn("stderr", captured)

    def test_ssh_base_has_non_interactive_timeout_options(self) -> None:
        args = argparse.Namespace(port="22", identity_file=None, target="user@example.com")
        command = deploy.ssh_base(args)

        self.assertIn("BatchMode=yes", command)
        self.assertIn("ConnectTimeout=10", command)
        self.assertIn("ConnectionAttempts=1", command)
        self.assertIn("NumberOfPasswordPrompts=0", command)
        self.assertIn("StrictHostKeyChecking=accept-new", command)

    def test_package_contains_runtime_app_files(self) -> None:
        package = deploy.package_app()
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
        missing = deploy.missing_prereqs(
            {
                "sudo": "ok",
                "docker": "ok",
                "compose": "missing",
                "network": "unknown",
            }
        )

        self.assertEqual(missing, ["Docker Compose", "outbound network"])

    def test_missing_prereqs_includes_passwordless_sudo(self) -> None:
        missing = deploy.missing_prereqs(
            {
                "sudo": "password_required",
                "docker": "ok",
                "compose": "ok",
                "network": "ok",
            }
        )

        self.assertEqual(missing, ["sudo password or non-interactive sudo"])

    def test_deployer_config_roundtrip_excludes_sudo_password(self) -> None:
        config_dir = Path(".test-tmp") / uuid4().hex
        config_dir.mkdir(parents=True, exist_ok=False)
        config = config_dir / ".deployer.json"
        args = argparse.Namespace(
            config=str(config),
            no_save_config=False,
            target="user@example.com",
            port="2222",
            identity_file="C:/Users/example/.ssh/id_ed25519",
            remote_root="/opt/nanobot-console",
            console_port="8787",
            saved_host_approval=False,
        )

        deploy.save_config(args, approved_host_changes=True)
        loaded = deploy.load_config(config)
        raw_json = json.loads(config.read_text(encoding="utf-8"))

        self.assertEqual(loaded["target"], "user@example.com")
        self.assertEqual(loaded["port"], "2222")
        self.assertEqual(loaded["approved_host_changes"], "true")
        self.assertNotIn("password", json.dumps(raw_json).lower())

    def test_apply_config_fills_missing_cli_values(self) -> None:
        args = argparse.Namespace(
            target=None,
            port=None,
            identity_file=None,
            remote_root=None,
            console_port=None,
        )

        deploy.apply_config(
            args,
            {
                "target": "user@example.com",
                "port": "2222",
                "identity_file": "key.pem",
                "remote_root": "/srv/nanobot",
                "console_port": "9876",
                "approved_host_changes": "true",
            },
        )

        self.assertEqual(args.target, "user@example.com")
        self.assertEqual(args.port, "2222")
        self.assertEqual(args.identity_file, "key.pem")
        self.assertEqual(args.remote_root, "/srv/nanobot")
        self.assertEqual(args.console_port, "9876")
        self.assertTrue(args.saved_host_approval)

    def test_run_sudo_shell_passes_password_via_stdin(self) -> None:
        args = argparse.Namespace(port="22", identity_file=None, target="user@example.com")
        captured: dict[str, object] = {}

        def fake_run(cmd, *, input_text=None):
            captured["cmd"] = cmd
            captured["input_text"] = input_text
            return subprocess.CompletedProcess(cmd, 0, "", "")

        original = deploy.run
        try:
            deploy.run = fake_run
            deploy.run_sudo_shell(args, "true", "secret-pass")
        finally:
            deploy.run = original

        command = " ".join(captured["cmd"])
        self.assertIn("sudo -S", command)
        self.assertNotIn("secret-pass", command)
        self.assertEqual(captured["input_text"], "secret-pass\n")

    def test_prompt_sudo_password_retries_without_storing_password(self) -> None:
        args = argparse.Namespace(yes=False)
        attempts: list[str] = []
        prompts = iter(["wrong-pass", "right-pass"])

        def fake_getpass(prompt: str) -> str:
            self.assertIn("Linux sudo password", prompt)
            return next(prompts)

        def fake_run_sudo_shell(args, command: str, sudo_password: str):
            attempts.append(sudo_password)
            if sudo_password == "wrong-pass":
                raise subprocess.CalledProcessError(1, command, stderr="Sorry, try again.")
            return subprocess.CompletedProcess(command, 0, "", "")

        original_getpass = deploy.getpass.getpass
        original_sudo = deploy.run_sudo_shell
        try:
            deploy.getpass.getpass = fake_getpass
            deploy.run_sudo_shell = fake_run_sudo_shell
            result = deploy.prompt_sudo_password(args)
        finally:
            deploy.getpass.getpass = original_getpass
            deploy.run_sudo_shell = original_sudo

        self.assertEqual(result, "right-pass")
        self.assertEqual(attempts, ["wrong-pass", "right-pass"])

    def test_bootstrap_with_sudo_preserves_script_exit_status(self) -> None:
        args = argparse.Namespace(remote_root="/opt/nanobot-console", console_port="8787")
        captured: dict[str, object] = {}

        def fake_upload_bootstrap_tmp(args):
            return "/tmp/bootstrap.sh"

        def fake_run_sudo_shell(args, command: str, sudo_password: str):
            captured["command"] = command
            captured["sudo_password"] = sudo_password
            return subprocess.CompletedProcess(command, 0, "", "")

        original_upload = deploy.upload_bootstrap_tmp
        original_sudo = deploy.run_sudo_shell
        try:
            deploy.upload_bootstrap_tmp = fake_upload_bootstrap_tmp
            deploy.run_sudo_shell = fake_run_sudo_shell
            deploy.run_bootstrap_with_sudo_password(args, "apply", "secret-pass")
        finally:
            deploy.upload_bootstrap_tmp = original_upload
            deploy.run_sudo_shell = original_sudo

        self.assertIn("status=$?", str(captured["command"]))
        self.assertIn("exit $status", str(captured["command"]))
        self.assertEqual(captured["sudo_password"], "secret-pass")

    def test_upload_scaffold_with_sudo_creates_remote_root(self) -> None:
        args = argparse.Namespace(
            target="user@example.com",
            port="22",
            identity_file=None,
            remote_root="/opt/nanobot-console",
        )
        captured: dict[str, object] = {}

        def fake_run(cmd, **kwargs):
            return subprocess.CompletedProcess(cmd, 0, "", "")

        def fake_run_sudo_shell(args, command: str, sudo_password: str):
            captured["command"] = command
            captured["sudo_password"] = sudo_password
            return subprocess.CompletedProcess(command, 0, "", "")

        original_run = deploy.run
        original_sudo = deploy.run_sudo_shell
        try:
            deploy.run = fake_run
            deploy.run_sudo_shell = fake_run_sudo_shell
            deploy.upload_scaffold(args, "secret-pass")
        finally:
            deploy.run = original_run
            deploy.run_sudo_shell = original_sudo

        self.assertIn("mkdir -p /opt/nanobot-console", str(captured["command"]))
        self.assertIn("install -m 0755", str(captured["command"]))
        self.assertIn("/opt/nanobot-console/consolectl", str(captured["command"]))
        self.assertEqual(captured["sudo_password"], "secret-pass")

    def test_bootstrap_runs_with_bash(self) -> None:
        args = argparse.Namespace(remote_root="/opt/test root", console_port="8787")
        captured: dict[str, str | None] = {}

        def fake_run_ssh(args, command: str, *, input_text: str | None = None):
            captured["command"] = command
            captured["input_text"] = input_text
            return None

        original = deploy.run_ssh
        try:
            deploy.run_ssh = fake_run_ssh
            deploy.run_bootstrap(args, "probe")
        finally:
            deploy.run_ssh = original

        self.assertIn("bash -s -- probe", str(captured["command"]))
        self.assertIn("/opt/test root", str(captured["command"]))
        self.assertIn("probe()", str(captured["input_text"]))
        self.assertNotIn("\r\n", str(captured["input_text"]))


if __name__ == "__main__":
    unittest.main()
