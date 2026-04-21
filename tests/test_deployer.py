from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEPLOYER = ROOT / "deployer" / "deploy.ps1"
BOOTSTRAP = ROOT / "deployer" / "remote" / "bootstrap.sh"
CONTROL = ROOT / "deployer" / "remote" / "consolectl.sh"
README = ROOT / "README.md"


class DeployerTest(unittest.TestCase):
    def test_powershell_deployer_is_the_only_operator_deployer(self) -> None:
        self.assertTrue(DEPLOYER.is_file())

        readme = README.read_text(encoding="utf-8")
        self.assertIn(".\\deployer\\deploy.ps1", readme)

    def test_powershell_deployer_uses_ssh_scp_and_remote_sudo(self) -> None:
        script = DEPLOYER.read_text(encoding="utf-8")

        self.assertIn("& ssh @cmdArgs", script)
        self.assertIn("& scp @cmdArgs", script)
        self.assertIn("sudo -S -p '' bash -lc", script)
        self.assertIn("sudo -n bash -lc", script)
        self.assertIn("Read-Host \"Remote Linux sudo password for the target user\" -AsSecureString", script)
        self.assertNotIn("python.exe", script.lower())
        self.assertNotIn("py -3", script)

    def test_powershell_deployer_prompts_for_human_defaults(self) -> None:
        script = DEPLOYER.read_text(encoding="utf-8")

        self.assertIn("function Configure-Interactive", script)
        self.assertIn('$ProvidedParameters = @{} + $PSBoundParameters', script)
        self.assertIn('Prompt-Value "SSH target, for example <user>@<vm-ip>"', script)
        self.assertIn('Prompt-Value "SSH port" $DEFAULT_PORT', script)
        self.assertIn('Prompt-Value "Remote deploy root on the VM" $DEFAULT_REMOTE_ROOT', script)
        self.assertIn('Prompt-Value "Console port" $DEFAULT_CONSOLE_PORT', script)
        self.assertIn('Prompt-Value "Console HTTPS domain, or press Enter for HTTP-only access" ""', script)
        self.assertIn('$answer.Trim().ToLowerInvariant() -ne "yes"', script)
        self.assertIn('Write-Host "Host changes were not approved. Exiting."', script)

    def test_powershell_deployer_uploads_only_runtime_sources(self) -> None:
        script = DEPLOYER.read_text(encoding="utf-8")
        staging = script.split("function New-AppUploadStaging", 1)[1].split("function ConsoleUrl", 1)[0]
        app_sources = script.split("$appSources = @(", 1)[1].split("Copy-Remote $appSources", 1)[0]

        self.assertIn("function Copy-FilteredTree", script)
        self.assertIn('$parts -contains "__pycache__"', script)
        self.assertIn('$_.Name -like "*.pyc"', script)
        self.assertIn('$_.FullName.Substring($sourcePrefix.Length)', script)
        self.assertNotIn("GetRelativePath", script)
        self.assertIn('"console"', staging)
        self.assertIn('"docker"', staging)
        self.assertIn('"Dockerfile"', staging)
        self.assertIn('(Join-Path $appStaging "console")', app_sources)
        self.assertIn('(Join-Path $appStaging "docker")', app_sources)
        self.assertIn('(Join-Path $appStaging "Dockerfile")', app_sources)
        self.assertNotIn("README.md", app_sources)
        self.assertNotIn("docker-compose.yml", app_sources)

    def test_deployer_does_not_delete_remote_app_directory(self) -> None:
        script = DEPLOYER.read_text(encoding="utf-8")

        self.assertNotIn("rm -rf $RemoteRootQ/app", script)
        self.assertIn("mkdir -p $RemoteRootQ/app", script)

    def test_bootstrap_has_required_remote_install_behavior(self) -> None:
        script = BOOTSTRAP.read_text(encoding="utf-8")

        self.assertIn("docker-compose-plugin", script)
        self.assertIn("docker-compose-v2", script)
        self.assertIn("docker-compose", script)
        self.assertIn("python3 docker.io", script)
        self.assertIn("docker_build=start", script)
        self.assertIn("docker_build=ok", script)
        self.assertIn("service_restart=start", script)
        self.assertIn("ExecStart=/usr/bin/python3 -m console", script)

    def test_bootstrap_supports_https_reverse_proxy_or_http_warning(self) -> None:
        script = BOOTSTRAP.read_text(encoding="utf-8")

        self.assertIn("CONSOLE_DOMAIN", script)
        self.assertIn("caddy", script)
        self.assertIn("reverse_proxy 127.0.0.1:$CONSOLE_PORT", script)
        self.assertIn("warning=http_only_console", script)

    def test_control_script_has_service_commands(self) -> None:
        script = CONTROL.read_text(encoding="utf-8")

        self.assertIn("restart|status|logs|bot-logs|url", script)
        self.assertIn("systemctl restart", script)
        self.assertIn("journalctl -u", script)
        self.assertIn("docker compose -p", script)
        self.assertIn("--timestamps", script)
        self.assertIn("nanobot-console", script)


if __name__ == "__main__":
    unittest.main()
