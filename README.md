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
py -3 deployer\deploy.py --domain console.example.com
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
| `--identity-file PATH` | SSH private key path, if you do not want to use the default key from `~/.ssh`. |
| `--remote-root PATH` | Install root on the target server. |
| `--console-port PORT` | HTTP port for the console UI. |
| `--domain DOMAIN` | Publish the console as `https://DOMAIN/` through a reverse proxy. |

### Preflight Checks

Preflight has two parts: what the operator must have ready before the deployer can work, and what the deployer checks or installs on the server.

#### Operator Prerequisites

The operator should have:

- Python 3 launcher on the operator machine;
- OpenSSH `ssh` and `scp` on the operator machine;
- a reachable Linux server or VM;
- SSH access to that server;
- SSH key login. If the key is not the default one from `~/.ssh`, pass it with `--identity-file PATH`;
- a remote user that can run `sudo`.

Optional manual checks:

```powershell
py -3 --version
ssh -V
scp
ssh <user>@<vm-ip>
ssh -o BatchMode=yes <user>@<vm-ip> "printf 'ssh=ok\n'"
ssh <user>@<vm-ip> "sudo true"
```

If one of these fails:

- install/fix missing `py`, `ssh`, or `scp` locally;
- fix VM networking, IP address, username, SSH server, or firewall if normal SSH fails;
- set up SSH key login if `BatchMode=yes` fails. If the key exists but is not the default key, pass its private-key path with `--identity-file PATH`;
- enter the Linux sudo password when the interactive deployer asks for it;
- use non-interactive sudo only when running with `--yes`.

If `BatchMode=yes` fails, one way to configure SSH key login is:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <user>@<vm-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

#### Deployer Checks And Installs

After SSH works, the deployer checks the server for:

- `sudo`;
- OS and CPU architecture;
- Docker Engine;
- Docker Compose;
- disk space;
- memory;
- outbound network access.

If Docker or Compose is missing and the operator approves host changes, the deployer attempts to install or repair them. It also creates or updates the console under the remote install root.

The deployer does not install Python, SSH, or SCP on the operator machine, and it does not fix unreachable VM networking or missing SSH access.

## Console Exposure

Without `--domain`, the console is served as plain HTTP on `http://<server>:<console-port>/`. Use that only for local/manual testing on a trusted network.

With `--domain console.example.com`, the deployer binds the console backend to `127.0.0.1`, attempts to install/configure Caddy, and publishes `https://console.example.com/`. The operator must point DNS to the server and allow inbound `80/tcp` and `443/tcp`.

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

## Two-Bot Isolation Check

Manual smoke test for a server that already has the console:

1. Create two bots with different Telegram tokens and allowlisted users.
2. Start both bots from the UI.
3. Send a Telegram message to each bot.
4. Confirm each bot has its own Activity and Runtime logs.
5. Stop one bot.
6. Confirm the stopped bot no longer responds and the other bot still responds.

Each bot should keep a separate directory under `/opt/nanobot-console/bots/<bot-id>/` and a separate Compose project named from that bot ID.

## Security

- Do not commit real secrets.
- Rotate any token that appears in chat, screenshots, terminal output, or logs.
- Keep the console private. Plain HTTP is for local/manual testing only; use HTTPS, VPN, SSH tunnel, firewall, or another access-control layer for non-local use.
- Use `--domain DOMAIN` when the console should be reachable as HTTPS on a real host.
- Telegram allowlist is required for bot start.
- Bot containers do not mount `docker.sock`.
- Bot containers run as a non-root app user.
- Bot state is isolated per bot under `/opt/nanobot-console/bots/<bot-id>/`.

## Development Checks

```powershell
docker compose config
py -3 -m unittest tests.test_deployer tests.test_deploy_engine tests.test_console_ui tests.test_runtime_image tests.test_redact
```
