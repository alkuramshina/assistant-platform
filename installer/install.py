#!/usr/bin/env python3
"""SSH bootstrap installer for the nanobot console prototype."""

from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from pathlib import Path


DEFAULT_REMOTE_ROOT = "/opt/nanobot-console"
ROOT = Path(__file__).resolve().parents[1]
REMOTE_BOOTSTRAP = ROOT / "installer" / "remote" / "bootstrap.sh"
VERSION = "prototype-phase-5"


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
    parser.add_argument("--dry-run", action="store_true", help="Probe and print planned changes only")
    parser.add_argument("--yes", action="store_true", help="Approve host changes without prompting")
    return parser.parse_args()


def ssh_base(args: argparse.Namespace) -> list[str]:
    cmd = ["ssh", "-p", str(args.port), "-o", "BatchMode=yes"]
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
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=check,
    )


def run_ssh(
    args: argparse.Namespace,
    remote_cmd: str,
    *,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return run([*ssh_base(args), remote_cmd], input_text=input_text)


def run_bootstrap(args: argparse.Namespace, mode: str) -> subprocess.CompletedProcess[str]:
    script = REMOTE_BOOTSTRAP.read_text(encoding="utf-8")
    remote_root = shlex.quote(args.remote_root)
    return run_ssh(args, f"sh -s -- {shlex.quote(mode)} {remote_root}", input_text=script)


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


def main() -> int:
    args = parse_args()
    if not REMOTE_BOOTSTRAP.exists():
        print(f"Missing remote bootstrap script: {REMOTE_BOOTSTRAP}", file=sys.stderr)
        return 2

    print(f"Target: {args.target}")
    print(f"Remote root: {args.remote_root}")
    print("Checking SSH connectivity...")
    run_ssh(args, "printf 'ssh=ok\\n'")

    print("Probing remote prerequisites...")
    probe_result = run_bootstrap(args, "probe")
    probe = parse_probe(probe_result.stdout)
    print_probe(probe)
    missing = missing_prereqs(probe)

    if args.dry_run:
        print()
        print("Dry-run only. Planned apply steps:")
        print(f"  - create/update {args.remote_root}")
        print("  - upload bootstrap.sh and VERSION scaffold files")
        if missing:
            print(f"  - prerequisite attention needed: {', '.join(missing)}")
        return 0

    if not confirm(args, missing):
        print("Aborted: host changes were not approved.")
        return 1

    print("Applying remote bootstrap...")
    apply_result = run_bootstrap(args, "apply")
    print(apply_result.stdout, end="")

    print("Uploading scaffold files...")
    upload_scaffold(args)

    print("Done.")
    print(f"Console scaffold: {args.remote_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
