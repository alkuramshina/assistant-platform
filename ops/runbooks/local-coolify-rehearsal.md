# Local Coolify Rehearsal

Goal: start Coolify locally on the current Docker Desktop/WSL2 machine and rehearse the Compose import path before the live Coolify control-plane validation phase.

This runbook is for Phase 03.1. It does not replace the later remote or live Coolify validation. Phase 03.1 is complete only when local Coolify actually starts and the UI is reachable.

## Safety Boundary

Local Coolify is a control-plane tool. It may need host-level Docker access to manage containers. That does not change the application rule: the `nanobot` service must not mount `/var/run/docker.sock`, must keep named volumes, and must avoid broad host bind mounts.

Do not paste real secret values into this file, `.planning`, screenshots, issue text, or logs. Real `OPENROUTER_API_KEY`, `TELEGRAM_TOKEN`, registry credentials, and related keys may be entered only through local runtime configuration or the Coolify UI.

## Preconditions

- Docker Desktop is installed and running.
- WSL2/Linux is available for the Coolify install path.
- Docker and Docker Compose are reachable from the selected environment.
- Port `8000` is available, or a different installer-provided local UI URL is recorded.
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

## Preflight

Run these checks before any install command:

```powershell
wsl -l -v
docker version
docker compose version
docker ps
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

Inside the selected WSL2/Linux environment, run where available:

```sh
uname -a
df -h
free -h || true
ss -ltnp | grep ':8000' || true
```

If Docker, WSL2/Linux, resources, or port availability cannot be verified, record the blocker in the Phase 03.1 UAT file and do not mark the phase complete.

## Install Approval Gate

Stop here before installation.

Coolify's official quick install is Linux/server-oriented and can require `sudo`, network access, Docker Engine changes, SSH setup, `/data/coolify`, Docker networks, and downloaded images.

Run installation only after explicit operator approval.

Preferred command inside the selected WSL2/Linux environment:

```sh
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | sudo bash
```

If this path is not suitable for the local machine, follow Coolify's manual installation docs and record the reason in the UAT file.

## Verify Local Coolify

After install or start, verify containers and UI:

```powershell
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"
Invoke-WebRequest -UseBasicParsing http://localhost:8000
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
