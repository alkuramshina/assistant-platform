# Nanobot Console

Nanobot Console deploys multiple isolated Telegram assistants on a Linux server or VM.

The operator runs one SSH deployer from this repo, opens the web console, enters bot settings, and starts bots from the UI.

```text
Linux server or VM -> SSH deployer -> web console -> Telegram bot -> activity logs
```

## Quick Start

From Windows PowerShell in the repo root:

```powershell
py -3 deployer\deploy.py
```

The deployer asks for the SSH target, checks the server, installs or updates the console, starts the service, and prints the UI URL.

For repeat deploys, run the same command again:

```powershell
py -3 deployer\deploy.py
```

Non-secret SSH/deploy settings are saved in `.deployer.json`. Sudo passwords, Telegram tokens, provider keys, and bot secrets are never stored there.

Detailed deployer guide: [`deployer/README.md`](deployer/README.md).

## Create A Bot

Open the printed console URL and create a bot with:

- bot name;
- Telegram bot token;
- allowed Telegram user IDs;
- provider API key;
- model preset;
- optional proxy URL, if the server cannot reach Telegram directly;
- optional system prompt.

Each bot gets its own Compose project, secrets, data directory, workspace, runtime logs, and activity logs.

## Telegram Connectivity

The server must reach Telegram Bot API:

```powershell
ssh <user>@<vm-ip> 'curl -I --max-time 10 https://api.telegram.org'
```

If general internet works but Telegram times out, run a VPN/proxy on the server and set the bot `Proxy URL` in the UI, for example:

```text
http://host.docker.internal:10801
```

## After Deploy

The deployer installs a helper on the server:

```bash
sudo /opt/nanobot-console/consolectl status
sudo /opt/nanobot-console/consolectl restart
sudo /opt/nanobot-console/consolectl logs
sudo /opt/nanobot-console/consolectl bot-logs <bot-id> 200
sudo /opt/nanobot-console/consolectl url
```

The web UI also shows:

- bot list and status;
- start/stop controls;
- activity logs with user requests and bot responses;
- runtime logs for startup, Telegram, provider, and compose diagnostics.

## Security Notes

- Do not commit real secrets.
- Rotate any token that appears in chat, screenshots, terminal output, or logs.
- Keep the console private. Plain HTTP is for local/manual testing only.
- Telegram allowlist is required for bot start.
- Bot containers do not mount `docker.sock`.
- Bot state is isolated per bot under `/opt/nanobot-console/bots/<bot-id>/`.

## Development Checks

```powershell
docker compose config
py -3 -m unittest tests.test_deployer tests.test_deploy_engine tests.test_console_ui tests.test_runtime_image tests.test_redact
```

Product summary: [`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md).
