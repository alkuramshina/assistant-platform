# Local Coolify Rehearsal

Goal: start Coolify on a local Linux VM and rehearse the Compose import path before the live Coolify control-plane validation phase.

This runbook is for Phase 03.1. It does not replace the later remote or live Coolify validation. Phase 03.1 is complete only when local Coolify actually starts and the UI is reachable.

## Safety Boundary

Local Coolify is a control-plane tool. It may need host-level Docker access to manage containers. That does not change the application rule: the `nanobot` service must not mount `/var/run/docker.sock`, must keep named volumes, and must avoid broad host bind mounts.

Do not paste real secret values into this file, `.planning`, screenshots, issue text, or logs. Real `OPENROUTER_API_KEY`, `TELEGRAM_TOKEN`, registry credentials, and related keys may be entered only through local runtime configuration or the Coolify UI.

## Preconditions

- A local Linux VM is available on the current machine.
- The VM runs Ubuntu LTS or another Coolify-supported Linux distribution.
- The VM has enough resources for a local control-plane rehearsal. Use at least 2 CPU cores, 2 GB RAM, and 30 GB disk as a practical minimum.
- The VM has network access to download packages and images.
- The VM is reachable from the host by SSH or by an equivalent VM console.
- Port `8000` is reachable from the host, or a different installer-provided local UI URL is recorded.
- Docker Engine is native to the VM and managed by `systemd` as `docker.service`.
- The private GHCR image path is available for rehearsal:

  ```text
  REGISTRY_IMAGE=ghcr.io/OWNER/assistant-platform
  IMAGE_TAG=sha-<git-sha>
  ```

- A read-only package pull credential for private GHCR is available to enter in Coolify.
- Real Telegram/OpenRouter values are available only for UI/runtime entry:

  ```text
  OPENROUTER_API_KEY
  TELEGRAM_TOKEN
  CHANNEL_ALLOW_FROM
  ```

## Local VM Shape

Use the VM tool already available on the workstation, such as Hyper-V, VirtualBox, VMware, or another local hypervisor. Keep the VM boring:

- Ubuntu Server LTS;
- 2 CPU cores minimum;
- 2 GB RAM minimum, 4 GB if available;
- 30 GB disk minimum, 40 GB if available;
- SSH enabled or console access available;
- network mode that makes port `8000` reachable from the Windows host, either bridged networking or NAT port forwarding.

The VM should behave like a small Linux server. Avoid Docker Desktop integration for this rehearsal because Coolify's installer needs to manage the Docker daemon through Linux service semantics.

## Preflight

Run these checks on the Windows host before any install command:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
Test-NetConnection <vm-ip> -Port 22
```

Run these checks inside the local Linux VM:

```sh
uname -a
df -h
free -h || true
systemctl is-system-running || true
systemctl status docker --no-pager || true
docker version
docker compose version
ss -ltnp | grep ':8000' || true
```

If Docker, Linux VM resources, `docker.service`, or port reachability cannot be verified, record the blocker in the Phase 03.1 UAT file and do not mark the phase complete.

## Install Approval Gate

Stop here before installation.

Coolify's official quick install is Linux/server-oriented and can require `sudo`, network access, Docker Engine changes, SSH setup, `/data/coolify`, Docker networks, and downloaded images.

Run installation only after explicit operator approval.

Preferred command inside the local Linux VM:

```sh
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
```

If `sudo` requires a password, run this command directly in an interactive Ubuntu terminal and enter the password there. Do not paste Linux passwords, installer-generated secrets, or token values into agent chat, docs, `.planning`, or logs.

The WSL2 + Docker Desktop integration path was tried and rejected for this project because the installer failed with `Failed to restart docker.service: Unit docker.service not found.` In that mode, Docker is available from Ubuntu, but the Docker daemon is not managed by a local `docker.service` inside Ubuntu.

Do not force the installer against Docker Desktop's internal `docker-desktop` distro or a WSL distro that only uses Docker Desktop integration.

If this path is not suitable for the local machine, follow Coolify's manual installation docs and record the reason in the UAT file.

## Verify Local Coolify

After install or start, verify containers and UI:

```powershell
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
Invoke-WebRequest -UseBasicParsing http://<vm-ip-or-localhost>:8000
```

If the installer prints a different local URL, use that exact URL and record only the URL, status, and non-secret evidence.

## UI Rehearsal Checklist

1. Open the local Coolify UI.
2. Create the first admin account immediately after first access.
3. Create a pilot project/environment rehearsal target.
4. Add or verify private GHCR pull access using a read-only credential.
5. Import this repository as a Docker Compose application.
6. Select `docker-compose.yml`.
7. Set image variables:

   ```text
   REGISTRY_IMAGE=ghcr.io/OWNER/assistant-platform
   IMAGE_TAG=sha-<git-sha>
   ```

8. Enter real provider/channel values only through Coolify/runtime UI:

   ```text
   OPENROUTER_API_KEY
   TELEGRAM_TOKEN
   CHANNEL_ALLOW_FROM
   ```

9. Do not add a public domain or host `ports:` mapping unless explicitly required and documented.
10. Record pass/fail with redacted evidence only.

## Completion Rule

Phase 03.1 can close only if:

- local Coolify starts;
- the local Coolify UI is reachable;
- the UI/project/environment/import rehearsal result is recorded;
- no real-looking secrets are stored in repository files.

If install/start fails, record the concrete blocker and leave the phase incomplete.
