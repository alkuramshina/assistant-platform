#!/usr/bin/env python3
"""SSH bootstrap installer for the nanobot console prototype."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


DEFAULT_REMOTE_ROOT = "/opt/nanobot-console"
ROOT = Path(__file__).resolve().parents[1]
REMOTE_BOOTSTRAP = ROOT / "installer" / "remote" / "bootstrap.sh"
VERSION = "prototype-phase-5"
PACKAGE_PATHS = [
    "console",
    "docker",
    "Dockerfile",
    "docker-compose.yml",
    "README.md",
    "docs/PROJECT_SUMMARY.md",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Install or update the nanobot console scaffold on a Linux server over SSH. "
            "Target format: user@host"
        )
    )
    parser.add_argument("target", help="SSH target, for example ubuntu@example.com")
    parser.add_argument("--port", default="22", help="SSH port, default: 22")
    parser.add_argument("--identity-file", help="SSH private key path")
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT, help="Remote install root")
    parser.add_argument("--console-port", default="8787", help="Console port, default: 8787")
    parser.add_argument("--dry-run", action="store_true", help="Probe and print planned changes only")
    parser.add_argument("--yes", action="store_true", help="Approve host changes without prompting")
    return parser.parse_args()


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
        check=check,
    )
    return subprocess.CompletedProcess(
        result.args,
        result.returncode,
        result.stdout.decode("utf-8", "replace"),
        result.stderr.decode("utf-8", "replace"),
    )


def print_command_failure(exc: subprocess.CalledProcessError) -> None:
    print("Command failed:", " ".join(shlex.quote(str(part)) for part in exc.cmd), file=sys.stderr)
    if exc.stdout:
        print("stdout:", file=sys.stderr)
        print(exc.stdout.rstrip(), file=sys.stderr)
    if exc.stderr:
        print("stderr:", file=sys.stderr)
        print(exc.stderr.rstrip(), file=sys.stderr)


def run_ssh(
    args: argparse.Namespace,
    remote_cmd: str,
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return run([*ssh_base(args), remote_cmd], input_text=input_text)


def run_bootstrap(args: argparse.Namespace, mode: str) -> subprocess.CompletedProcess[str]:
    script = REMOTE_BOOTSTRAP.read_text(encoding="utf-8").replace("\r\n", "\n")
    remote_root = shlex.quote(args.remote_root)
    console_port = shlex.quote(str(args.console_port))
    return run_ssh(args, f"bash -s -- {shlex.quote(mode)} {remote_root} {console_port}", input_text=script)


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
    print()
    print("Planned host changes:")
    print(f"  - create/update {args.remote_root}")
    print("  - upload installer-controlled scaffold files")
    if missing:
        print(f"  - attempt prerequisite install/repair: {', '.join(missing)}")
    answer = input("Approve these host changes? Type 'yes' to continue: ").strip().lower()
    return answer == "yes"


def upload_scaffold(args: argparse.Namespace) -> None:
    remote_tmp = "/tmp/nanobot-console-bootstrap.sh"
    run([*scp_base(args), str(REMOTE_BOOTSTRAP), f"{args.target}:{remote_tmp}"])

    remote_root = shlex.quote(args.remote_root)
    remote_tmp_q = shlex.quote(remote_tmp)
    version_q = shlex.quote(VERSION)
    command = (
        f"sudo install -m 0755 {remote_tmp_q} {remote_root}/bootstrap.sh && "
        f"printf '%s\\n' {version_q} | sudo tee {remote_root}/VERSION >/dev/null && "
        f"sudo rm -f {remote_tmp_q}"
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


def upload_app(args: argparse.Namespace) -> None:
    package = package_app()
    remote_tmp = "/tmp/nanobot-console-app.tar.gz"
    try:
        run([*scp_base(args), str(package), f"{args.target}:{remote_tmp}"])
    finally:
        package.unlink(missing_ok=True)

    remote_root = shlex.quote(args.remote_root)
    remote_tmp_q = shlex.quote(remote_tmp)
    command = (
        f"sudo rm -rf {remote_root}/app && "
        f"sudo mkdir -p {remote_root}/app && "
        f"sudo tar -xzf {remote_tmp_q} -C {remote_root}/app && "
        f"sudo rm -f {remote_tmp_q}"
    )
    run_ssh(args, command)


def main() -> int:
    args = parse_args()
    if not REMOTE_BOOTSTRAP.exists():
        print(f"Missing remote bootstrap script: {REMOTE_BOOTSTRAP}", file=sys.stderr)
        return 2

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
        print("Installer uses BatchMode=yes, so password prompts are disabled.")
        print("Use SSH key login or pass --identity-file PATH_TO_KEY.")
        return 1

    print("Probing remote prerequisites...")
    try:
        probe_result = run_bootstrap(args, "probe")
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1
    probe = parse_probe(probe_result.stdout)
    print_probe(probe)
    missing = missing_prereqs(probe)

    if args.dry_run:
        print()
        print("Dry-run only. Planned apply steps:")
        print(f"  - create/update {args.remote_root}")
        print("  - upload app package")
        print("  - install/update console systemd service")
        print("  - build/refresh nanobot-enterprise-pilot:dev image")
        print(f"  - print UI URL on port {args.console_port}")
        if missing:
            print(f"  - prerequisite attention needed: {', '.join(missing)}")
        return 0

    if not confirm(args, missing):
        print("Aborted: host changes were not approved.")
        return 1

    print("Applying remote bootstrap...")
    try:
        apply_result = run_bootstrap(args, "apply")
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1
    print(apply_result.stdout, end="")

    print("Uploading bootstrap scaffold...")
    try:
        upload_scaffold(args)
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1

    print("Uploading app package...")
    try:
        upload_app(args)
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1

    print("Finalizing console service...")
    try:
        finalize_result = run_bootstrap(args, "finalize")
    except subprocess.CalledProcessError as exc:
        print_command_failure(exc)
        return 1
    print(finalize_result.stdout, end="")

    print("Done.")
    print(f"Console root: {args.remote_root}")
    print(f"Console URL: http://{args.target.split('@')[-1]}:{args.console_port}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
