#!/usr/bin/env python3
"""SSH deployer for Nanobot Console."""

from __future__ import annotations

import argparse
import getpass
import json
import shlex
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


DEFAULT_REMOTE_ROOT = "/opt/nanobot-console"
ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / ".deployer.json"
REMOTE_BOOTSTRAP = ROOT / "deployer" / "remote" / "bootstrap.sh"
REMOTE_CONTROL = ROOT / "deployer" / "remote" / "consolectl.sh"
VERSION = "nanobot-console"
CONFIG_KEYS = ("target", "port", "identity_file", "remote_root", "console_port", "approved_host_changes")
PACKAGE_PATHS = [
    "console",
    "docker",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Deploy or update Nanobot Console on a Linux server over SSH. "
            "Target format: user@host"
        )
    )
    parser.add_argument("target", nargs="?", help="SSH target, for example ubuntu@example.com")
    parser.add_argument("--port", help="SSH port, default: 22")
    parser.add_argument("--identity-file", help="SSH private key path")
    parser.add_argument("--remote-root", help=f"Remote deploy root, default: {DEFAULT_REMOTE_ROOT}")
    parser.add_argument("--console-port", help="Console port, default: 8787")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Local deployer config path")
    parser.add_argument("--no-save-config", action="store_true", help="Do not write local deployer config")
    parser.add_argument("--reset-config", action="store_true", help="Ignore saved deployer config for this run")
    parser.add_argument("--dry-run", action="store_true", help="Probe and print planned changes only")
    parser.add_argument("--yes", action="store_true", help="Non-interactive apply: approve host changes and fail instead of retry prompts")
    return parser.parse_args()


def load_config(path: str | Path, *, reset: bool = False) -> dict[str, str]:
    if reset:
        return {}
    config_path = Path(path)
    if not config_path.is_file():
        return {}
    try:
        raw = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {key: str(raw[key]) for key in CONFIG_KEYS if key in raw and raw[key] not in (None, "")}


def apply_config(args: argparse.Namespace, config: dict[str, str]) -> None:
    args.target = args.target or config.get("target")
    args.port = args.port or config.get("port") or "22"
    args.identity_file = args.identity_file or config.get("identity_file") or None
    args.remote_root = args.remote_root or config.get("remote_root") or DEFAULT_REMOTE_ROOT
    args.console_port = args.console_port or config.get("console_port") or "8787"
    args.saved_host_approval = config.get("approved_host_changes") == "true"


def save_config(args: argparse.Namespace, *, approved_host_changes: bool | None = None) -> None:
    if args.no_save_config:
        return
    config_path = Path(args.config)
    data = {
        "target": args.target,
        "port": str(args.port),
        "remote_root": args.remote_root,
        "console_port": str(args.console_port),
    }
    if args.identity_file:
        data["identity_file"] = args.identity_file
    approval = approved_host_changes if approved_host_changes is not None else getattr(args, "saved_host_approval", False)
    if approval:
        data["approved_host_changes"] = "true"
    config_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Saved deployer config: {config_path}")


def ssh_base(args: argparse.Namespace) -> list[str]:
    cmd = [
        "ssh",
        "-p",
        str(args.port),
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ConnectionAttempts=1",
        "-o",
        "NumberOfPasswordPrompts=0",
        "-o",
        "StrictHostKeyChecking=accept-new",
    ]
    if args.identity_file:
        cmd.extend(["-i", args.identity_file])
    cmd.append(args.target)
    return cmd


def scp_base(args: argparse.Namespace) -> list[str]:
    cmd = ["scp", "-P", str(args.port)]
    if args.identity_file:
        cmd.extend(["-i", args.identity_file])
    return cmd


def run(
    cmd: list[str],
    *,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    if input_text is None:
        return subprocess.run(
            cmd,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=check,
        )

    result = subprocess.run(
        cmd,
        input=input_text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    completed = subprocess.CompletedProcess(
        result.args,
        result.returncode,
        result.stdout.decode("utf-8", "replace"),
        result.stderr.decode("utf-8", "replace"),
    )
    if check and completed.returncode != 0:
        raise subprocess.CalledProcessError(
            completed.returncode,
            completed.args,
            output=completed.stdout,
            stderr=completed.stderr,
        )
    return completed


def run_stream(
    cmd: list[str],
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[None]:
    input_bytes = input_text.encode("utf-8") if input_text is not None else None
    return subprocess.run(cmd, input=input_bytes, check=True)


def print_command_failure(exc: subprocess.CalledProcessError) -> None:
    print("Command failed:", " ".join(shlex.quote(str(part)) for part in exc.cmd), file=sys.stderr)
    if exc.stdout:
        print("stdout:", file=sys.stderr)
        print(exc.stdout.rstrip(), file=sys.stderr)
    if exc.stderr:
        print("stderr:", file=sys.stderr)
        print(exc.stderr.rstrip(), file=sys.stderr)


def prompt_value(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    value = input(f"{label}{suffix}: ").strip()
    return value or default


def configure_interactive(args: argparse.Namespace) -> None:
    if args.target:
        return
    print("Interactive deployer")
    args.target = prompt_value("SSH target, for example <user>@<vm-ip>")
    args.port = prompt_value("SSH port", str(args.port))
    args.identity_file = (
        prompt_value("SSH identity file path, or press Enter to use the default SSH key", args.identity_file or "")
        or None
    )
    args.remote_root = prompt_value(
        "Remote deploy root on the VM, or press Enter to use /opt/nanobot-console",
        args.remote_root,
    )
    args.console_port = prompt_value("Console port", str(args.console_port))


def wait_for_retry(args: argparse.Namespace, reason: str) -> bool:
    if args.yes:
        return False
    answer = input(f"{reason}. Press Enter after fixing to retry, or type q to quit: ").strip().lower()
    return answer not in {"q", "quit", "n", "no"}


def print_sudo_help(args: argparse.Namespace) -> None:
    print()
    print("Remote sudo is not non-interactive.")
    print("SSH key login solves SSH authentication only; it does not remove the sudo password prompt.")
    if args.yes:
        print("Rerun without --yes to enter a sudo password interactively, or configure non-interactive sudo by your infrastructure policy.")
    else:
        print("Interactive deployer can use your sudo password for this deploy session without storing it.")


def run_ssh(
    args: argparse.Namespace,
    remote_cmd: str,
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return run([*ssh_base(args), remote_cmd], input_text=input_text)


def run_ssh_stream(
    args: argparse.Namespace,
    remote_cmd: str,
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[None]:
    return run_stream([*ssh_base(args), remote_cmd], input_text=input_text)


def run_sudo_shell(
    args: argparse.Namespace,
    remote_cmd: str,
    sudo_password: str,
) -> subprocess.CompletedProcess[str]:
    command = f"sudo -S -p '' bash -lc {shlex.quote(remote_cmd)}"
    return run_ssh(args, command, input_text=f"{sudo_password}\n")


def run_sudo_shell_stream(
    args: argparse.Namespace,
    remote_cmd: str,
    sudo_password: str,
) -> subprocess.CompletedProcess[None]:
    command = f"sudo -S -p '' bash -lc {shlex.quote(remote_cmd)}"
    return run_ssh_stream(args, command, input_text=f"{sudo_password}\n")


def prompt_sudo_password(args: argparse.Namespace) -> str | None:
    if args.yes:
        return None
    for attempt in range(1, 4):
        password = getpass.getpass("Remote Linux sudo password for the target user, blank to abort: ")
        if not password:
            return None
        try:
            run_sudo_shell(args, "true", password)
        except subprocess.CalledProcessError:
            remaining = 3 - attempt
            if remaining:
                print(f"Sudo password was not accepted. Try again ({remaining} attempts left).")
                continue
            print("Sudo password was not accepted.")
            return None
        return password
    return None


def run_bootstrap(args: argparse.Namespace, mode: str) -> subprocess.CompletedProcess[str]:
    script = REMOTE_BOOTSTRAP.read_text(encoding="utf-8").replace("\r\n", "\n")
    remote_root = shlex.quote(args.remote_root)
    console_port = shlex.quote(str(args.console_port))
    return run_ssh(args, f"bash -s -- {shlex.quote(mode)} {remote_root} {console_port}", input_text=script)


def upload_bootstrap_tmp(args: argparse.Namespace) -> str:
    remote_tmp = "/tmp/nanobot-console-bootstrap.sh"
    script = REMOTE_BOOTSTRAP.read_text(encoding="utf-8").replace("\r\n", "\n")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False) as tmp:
        tmp.write(script)
        tmp_path = Path(tmp.name)
    try:
        run([*scp_base(args), str(tmp_path), f"{args.target}:{remote_tmp}"])
    finally:
        tmp_path.unlink(missing_ok=True)
    return remote_tmp


def upload_text_tmp(args: argparse.Namespace, source: Path, remote_tmp: str) -> str:
    text = source.read_text(encoding="utf-8").replace("\r\n", "\n")
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", newline="\n", delete=False) as tmp:
        tmp.write(text)
        tmp_path = Path(tmp.name)
    try:
        run([*scp_base(args), str(tmp_path), f"{args.target}:{remote_tmp}"])
    finally:
        tmp_path.unlink(missing_ok=True)
    return remote_tmp


def run_bootstrap_with_sudo_password(
    args: argparse.Namespace,
    mode: str,
    sudo_password: str,
) -> subprocess.CompletedProcess[str]:
    remote_tmp = upload_bootstrap_tmp(args)
    remote_root = shlex.quote(args.remote_root)
    console_port = shlex.quote(str(args.console_port))
    remote_tmp_q = shlex.quote(remote_tmp)
    return run_sudo_shell(
        args,
        (
            f"bash {remote_tmp_q} {shlex.quote(mode)} {remote_root} {console_port}; "
            "status=$?; "
            f"rm -f {remote_tmp_q}; "
            "exit $status"
        ),
        sudo_password,
    )


def run_bootstrap_stream(args: argparse.Namespace, mode: str) -> subprocess.CompletedProcess[None]:
    script = REMOTE_BOOTSTRAP.read_text(encoding="utf-8").replace("\r\n", "\n")
    remote_root = shlex.quote(args.remote_root)
    console_port = shlex.quote(str(args.console_port))
    return run_ssh_stream(
        args,
        f"bash -s -- {shlex.quote(mode)} {remote_root} {console_port}",
        input_text=script,
    )


def run_bootstrap_with_sudo_password_stream(
    args: argparse.Namespace,
    mode: str,
    sudo_password: str,
) -> subprocess.CompletedProcess[None]:
    remote_tmp = upload_bootstrap_tmp(args)
    remote_root = shlex.quote(args.remote_root)
    console_port = shlex.quote(str(args.console_port))
    remote_tmp_q = shlex.quote(remote_tmp)
    return run_sudo_shell_stream(
        args,
        (
            f"bash {remote_tmp_q} {shlex.quote(mode)} {remote_root} {console_port}; "
            "status=$?; "
            f"rm -f {remote_tmp_q}; "
            "exit $status"
        ),
        sudo_password,
    )


def parse_probe(output: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in output.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip()
    return result


def print_probe(probe: dict[str, str]) -> None:
    print("Probe:")
    for key in sorted(probe):
        print(f"  {key}: {probe[key]}")


def missing_prereqs(probe: dict[str, str]) -> list[str]:
    missing: list[str] = []
    if probe.get("sudo") != "ok":
        missing.append("sudo password or non-interactive sudo")
    if probe.get("docker") != "ok":
        missing.append("Docker Engine")
    if probe.get("compose") != "ok":
        missing.append("Docker Compose")
    if probe.get("network") != "ok":
        missing.append("outbound network")
    return missing


def confirm(args: argparse.Namespace, missing: list[str]) -> bool:
    if args.yes:
        return True
    if getattr(args, "saved_host_approval", False):
        print()
        print(f"Using saved host-change approval from {args.config}.")
        return True
    print()
    print("Planned host changes:")
    print(f"  - create/update {args.remote_root}")
    print("  - upload deployer-controlled scaffold files")
    if missing:
            print(f"  - attempt prerequisite setup/repair: {', '.join(missing)}")
    answer = input("Approve these host changes? Type 'yes' to continue: ").strip().lower()
    return answer == "yes"


def upload_scaffold(args: argparse.Namespace, sudo_password: str | None = None) -> None:
    remote_tmp = upload_text_tmp(args, REMOTE_BOOTSTRAP, "/tmp/nanobot-console-bootstrap.sh")
    remote_ctl_tmp = upload_text_tmp(args, REMOTE_CONTROL, "/tmp/nanobot-console-consolectl.sh")

    remote_root = shlex.quote(args.remote_root)
    remote_tmp_q = shlex.quote(remote_tmp)
    remote_ctl_tmp_q = shlex.quote(remote_ctl_tmp)
    version_q = shlex.quote(VERSION)
    if sudo_password:
        command = (
            f"mkdir -p {remote_root} && "
            f"install -m 0755 {remote_tmp_q} {remote_root}/bootstrap.sh && "
            f"install -m 0755 {remote_ctl_tmp_q} {remote_root}/consolectl && "
            f"printf '%s\\n' {version_q} | tee {remote_root}/VERSION >/dev/null && "
            f"rm -f {remote_tmp_q} {remote_ctl_tmp_q}"
        )
        run_sudo_shell(args, command, sudo_password)
        return

    command = (
        f"sudo install -m 0755 {remote_tmp_q} {remote_root}/bootstrap.sh && "
        f"sudo install -m 0755 {remote_ctl_tmp_q} {remote_root}/consolectl && "
        f"printf '%s\\n' {version_q} | sudo tee {remote_root}/VERSION >/dev/null && "
        f"sudo rm -f {remote_tmp_q} {remote_ctl_tmp_q}"
    )
    run_ssh(args, command)


def package_app() -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix="nanobot-console-", suffix=".tar.gz", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()
    with tarfile.open(tmp_path, "w:gz") as archive:
        for item in PACKAGE_PATHS:
            source = ROOT / item
            if source.exists():
                archive.add(source, arcname=item)
    return tmp_path


def upload_app(args: argparse.Namespace, sudo_password: str | None = None) -> None:
    package = package_app()
    remote_tmp = "/tmp/nanobot-console-app.tar.gz"
    try:
        run([*scp_base(args), str(package), f"{args.target}:{remote_tmp}"])
    finally:
        package.unlink(missing_ok=True)

    remote_root = shlex.quote(args.remote_root)
    remote_tmp_q = shlex.quote(remote_tmp)
    if sudo_password:
        command = (
            f"rm -rf {remote_root}/app && "
            f"mkdir -p {remote_root}/app && "
            f"tar -xzf {remote_tmp_q} -C {remote_root}/app && "
            f"rm -f {remote_tmp_q}"
        )
        run_sudo_shell(args, command, sudo_password)
        return

    command = (
        f"sudo rm -rf {remote_root}/app && "
        f"sudo mkdir -p {remote_root}/app && "
        f"sudo tar -xzf {remote_tmp_q} -C {remote_root}/app && "
        f"sudo rm -f {remote_tmp_q}"
    )
    run_ssh(args, command)


def main() -> int:
    args = parse_args()
    apply_config(args, load_config(args.config, reset=args.reset_config))
    configure_interactive(args)
    if not args.target:
        print("Missing SSH target.", file=sys.stderr)
        return 2
    if not REMOTE_BOOTSTRAP.exists():
        print(f"Missing remote bootstrap script: {REMOTE_BOOTSTRAP}", file=sys.stderr)
        return 2
    if not REMOTE_CONTROL.exists():
        print(f"Missing remote control script: {REMOTE_CONTROL}", file=sys.stderr)
        return 2

    sudo_password: str | None = None
    while True:
        print(f"Target: {args.target}")
        print(f"Remote root: {args.remote_root}")
        print("Checking SSH connectivity...")
        try:
            run_ssh(args, "printf 'ssh=ok\\n'")
        except subprocess.CalledProcessError as exc:
            print_command_failure(exc)
            print()
            print("SSH check failed.")
            print("Try this from PowerShell first:")
            print(f"  ssh -p {args.port} {args.target}")
            print()
            print("Deployer uses BatchMode=yes, so password prompts are disabled.")
            print("Use SSH key login or pass --identity-file PATH_TO_KEY.")
            if wait_for_retry(args, "SSH check failed"):
                continue
            return 1

        print("Probing remote prerequisites...")
        try:
            probe_result = run_bootstrap(args, "probe")
        except subprocess.CalledProcessError as exc:
            print_command_failure(exc)
            if wait_for_retry(args, "Remote probe failed"):
                continue
            return 1
        probe = parse_probe(probe_result.stdout)
        print_probe(probe)
        save_config(args)
        missing = missing_prereqs(probe)
        if args.dry_run:
            break
        if probe.get("sudo") != "ok":
            print_sudo_help(args)
            sudo_password = prompt_sudo_password(args)
            if sudo_password:
                missing = [item for item in missing if item != "sudo password or non-interactive sudo"]
                break
            if wait_for_retry(args, "Sudo password was not accepted"):
                continue
            return 1
        break

    if args.dry_run:
        print()
        print("Dry-run only. Planned apply steps:")
        print(f"  - create/update {args.remote_root}")
        print("  - upload app package")
        print("  - deploy/update console systemd service")
        print("  - build/refresh nanobot-enterprise-pilot:dev image")
        print(f"  - print UI URL on port {args.console_port}")
        if missing:
            print(f"  - prerequisite attention needed: {', '.join(missing)}")
        return 0

    approved = confirm(args, missing)
    if not approved:
        print("Aborted: host changes were not approved.")
        return 1
    save_config(args, approved_host_changes=True)

    print("Applying remote bootstrap...")
    try:
        if sudo_password:
            run_bootstrap_with_sudo_password_stream(args, "apply", sudo_password)
        else:
            run_bootstrap_stream(args, "apply")
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1

    print("Uploading bootstrap scaffold...")
    try:
        upload_scaffold(args, sudo_password)
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1

    print("Uploading app package...")
    try:
        upload_app(args, sudo_password)
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1

    print("Finalizing console service...")
    try:
        if sudo_password:
            run_bootstrap_with_sudo_password_stream(args, "finalize", sudo_password)
        else:
            run_bootstrap_stream(args, "finalize")
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1

    print("Done.")
    print(f"Console root: {args.remote_root}")
    print(f"Console URL: http://{args.target.split('@')[-1]}:{args.console_port}/")
    print(f"Control command: sudo {args.remote_root}/consolectl status")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
