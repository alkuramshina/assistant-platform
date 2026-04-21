# Nanobot Console

Nanobot Console deploys isolated Telegram assistants on a customer-provided Linux server or VM.

The operator runs one SSH deployer, opens the web UI, enters bot settings, and starts bots from the console.

```text
Linux server or VM -> SSH deployer -> web console -> Telegram bot -> activity logs
```

## What It Does

- bootstraps or updates a Linux server over SSH;
- runs a small console UI and API;
- creates per-bot Docker Compose projects;
- stores Telegram/provider secrets as server-side files;
- starts/stops bots from the UI;
- shows Activity logs and Runtime logs per selected bot.

Each bot gets its own Compose project, secrets, data directory, workspace, runtime logs, and activity logs.

## Quick Start

```powershell
py -3 deployer\deploy.py
```

The deployer asks for the SSH target, checks the server, installs or updates the console, starts the service, and prints the UI URL.

Repeat deploys use the same command. Non-secret SSH/deploy settings are saved in `.deployer.json`; sudo passwords, Telegram tokens, provider keys, and bot secrets are not stored there.

## Deployer

Target server requirements:

- Ubuntu-compatible Linux;
- SSH server enabled;
- target user can run `sudo`;
- Docker Engine and Docker Compose, or permission for the deployer to install them;
- outbound network access.

Common commands:

```powershell
py -3 deployer\deploy.py                         # install/update
py -3 deployer\deploy.py --dry-run               # probe only
py -3 deployer\deploy.py <user>@<vm-ip>          # explicit target
py -3 deployer\deploy.py --reset-config          # ignore saved settings
py -3 deployer\deploy.py --no-save-config        # do not write .deployer.json
py -3 deployer\deploy.py <user>@<vm-ip> --yes    # non-interactive, requires key login and non-interactive sudo
```

Useful flags:

| Flag | Meaning |
|------|---------|
| `--dry-run` | Probe the host and print planned actions. |
| `--yes` | Approve changes and fail instead of prompting. |
| `--reset-config` | Ignore `.deployer.json` for this run. |
| `--no-save-config` | Do not write `.deployer.json`. |
| `--config PATH` | Use a different local deployer config file. |
| `--port PORT` | SSH port. |
| `--identity-file PATH` | SSH private key path. |
| `--remote-root PATH` | Install root on the target server. |
| `--console-port PORT` | HTTP port for the console UI. |

### Preflight Checks

The deployer runs its own SSH, sudo, Docker, Compose, disk, memory, and network checks. If Docker or Compose is missing and the operator approves host changes, the deployer attempts to install them.

The commands below are optional manual checks run by the operator from the machine where the deployer will be launched. Run them before the first deploy if the server is new, or after the deployer reports an SSH/sudo/connectivity error.

They answer three questions:

- does the operator machine have Python, SSH, and SCP;
- can the operator log in to the server over SSH without an interactive SSH password prompt;
- can the remote user run `sudo`.

```powershell
py -3 --version
ssh -V
scp
ssh <user>@<vm-ip>
ssh -o BatchMode=yes <user>@<vm-ip> "printf 'ssh=ok\n'"
ssh <user>@<vm-ip> "sudo true"
```

Expected operator actions:

- if `py`, `ssh`, or `scp` is missing, install/fix it on the operator machine;
- if normal `ssh <user>@<vm-ip>` fails, fix VM networking, IP address, username, SSH server, or firewall;
- if `BatchMode=yes` fails, set up SSH key login or pass `--identity-file`;
- if `sudo true` asks for a password, that is okay for interactive deploys: the deployer will ask for the Linux sudo password for this session and will not store it;
- if using `--yes`, `sudo true` must work without a password because non-interactive mode cannot prompt.

If `BatchMode=yes` fails, configure SSH key login:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <user>@<vm-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

## Create A Bot

Open the printed console URL and create a bot with:

- bot name;
- Telegram bot token;
- allowed Telegram user IDs;
- provider API key;
- model preset;
- optional timezone;
- optional proxy URL, if the server cannot reach Telegram directly;
- optional system prompt.

Click `Start`, then message the bot from an allowlisted Telegram account.

The UI shows:

- bot list and status;
- selected bot details;
- start/stop controls;
- Activity logs with user requests and bot responses;
- Runtime logs for startup, Telegram, provider, and Compose diagnostics.

## Telegram Connectivity

The server must reach Telegram Bot API.

```powershell
ssh <user>@<vm-ip> 'curl -I --max-time 10 https://api.telegram.org'
```

If general internet works but Telegram times out, run a VPN/proxy on the server and set the bot `Proxy URL` in the UI, for example:

```text
http://host.docker.internal:10801
```

## Console API

The UI uses the same local JSON API:

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | health check |
| `GET` | `/api/bots` | list bots |
| `POST` | `/api/bots` | create bot and write secret files |
| `GET` | `/api/bots/<id>` | fetch one bot |
| `POST` | `/api/bots/<id>/start` | start selected bot |
| `POST` | `/api/bots/<id>/stop` | stop selected bot |
| `GET` | `/api/bots/<id>/logs?limit=100` | Activity logs |
| `POST` | `/api/bots/<id>/logs` | Activity sink used by bot runtime |
| `GET` | `/api/bots/<id>/runtime-logs?tail=200` | Docker runtime logs |

Secret values are never returned by the API. Submitted tokens/keys are written under the server-side secret root.

## Server Control

The deployer installs a helper on the server:

```bash
sudo /opt/nanobot-console/consolectl status
sudo /opt/nanobot-console/consolectl restart
sudo /opt/nanobot-console/consolectl logs
sudo /opt/nanobot-console/consolectl bot-logs <bot-id> 200
sudo /opt/nanobot-console/consolectl url
```

## Security

- Do not commit real secrets.
- Rotate any token that appears in chat, screenshots, terminal output, or logs.
- Keep the console private. Plain HTTP is for local/manual testing only; use HTTPS, VPN, SSH tunnel, firewall, or another access-control layer for non-local use.
- Telegram allowlist is required for bot start.
- Bot containers do not mount `docker.sock`.
- Bot containers run as a non-root app user.
- Bot state is isolated per bot under `/opt/nanobot-console/bots/<bot-id>/`.

## Scope

In scope:

- SSH deployer;
- local console UI/API;
- per-bot Compose runtime;
- Telegram bot channel;
- OpenRouter-compatible provider presets;
- Activity and Runtime logs.

Out of scope:

- Coolify;
- Kubernetes;
- hosted SaaS control plane;
- multi-node orchestration;
- enterprise RBAC/SSO;
- full backup product.

## Development Checks

```powershell
docker compose config
py -3 -m unittest tests.test_deployer tests.test_deploy_engine tests.test_console_ui tests.test_runtime_image tests.test_redact
```
