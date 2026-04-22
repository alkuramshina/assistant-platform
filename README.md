# Nanobot Console

Nanobot Console installs a small web console on a customer-provided Linux server. From that console, an operator creates isolated Telegram assistants, stores their secrets server-side, and starts or stops each bot.

```text
operator PC -> SSH/SCP deployer -> Linux server -> web console -> Telegram bots
```

Each bot gets its own Docker Compose project, data directory, workspace, secret files, runtime logs, and activity logs.

## Install Or Update

Run the deployer from PowerShell on the operator machine:

```powershell
.\deployer\deploy.ps1
```

The deployer asks for:

- SSH target, for example `ubuntu@203.0.113.10`;
- SSH port, default `22`;
- remote install root, default `/opt/nanobot-console`;
- console HTTP port, default `8787`;
- optional HTTPS domain.

It then packages the runtime files into one `tar.gz`, uploads it with `scp`, runs the remote bootstrap over `ssh`, asks for host-change approval, asks for the remote `sudo` password once if needed, starts the service, and prints the console URL.

Only the operator machine needs `ssh`, `scp`, and `tar`. Python runs on the server; the remote bootstrap installs `python3`, Docker Engine, and Docker Compose when needed and approved.

## How Deployment Works

Deployment has two layers: the PowerShell deployer installs the Nanobot Console on the VM, and the console starts each bot as its own Docker Compose project.

The local deployer packages `deployer/remote/bootstrap.sh`, `deployer/remote/consolectl.sh`, `console/`, `docker/`, and `Dockerfile` into a temporary `tar.gz`. While packaging, it skips Python cache directories and compiled bytecode. The archive is uploaded to `/tmp/nanobot-console-upload.tar.gz`, extracted under `/tmp/nanobot-console-upload`, and the remote bootstrap first runs in `probe` mode to report OS, Docker, Compose, sudo, disk, memory, and basic network status.

After approval, bootstrap `apply` installs missing host prerequisites with `apt-get`, including `python3`, Docker Engine, and Docker Compose where needed. It creates the install layout under `/opt/nanobot-console`, including `app/`, `bots/`, `secrets/`, `templates/`, and `logs/`. The deployer then copies the uploaded app files into `/opt/nanobot-console/app`.

Bootstrap `finalize` builds the runtime container image on the server:

```bash
sudo docker build -t nanobot-enterprise-pilot:dev /opt/nanobot-console/app
```

That image comes from the repository `Dockerfile`. It uses `python:3.12-slim`, installs `nanobot-ai==0.1.4.post5`, copies `docker/entrypoint.sh`, `docker/generate_config.py`, and `docker/sitecustomize.py`, creates a non-root `app` user with uid `1000`, and runs containers as that user.

The console itself is not run in Docker. Bootstrap writes a `nanobot-console` systemd unit that runs:

```bash
python3 -m console --db /opt/nanobot-console/console.db --bot-root /opt/nanobot-console/bots --secret-root /opt/nanobot-console/secrets --host <bind-host> --port <console-port>
```

Without a domain, the console binds to `0.0.0.0:<console-port>`. With a domain, it binds to `127.0.0.1:<console-port>` and Caddy is configured as the HTTPS reverse proxy.

When an operator creates a bot in the web console, the API stores the bot record in SQLite and writes the Telegram token and provider API key into server-side secret files. When the operator clicks `Start`, the console validates that Telegram allowlist and secret refs exist, creates `/opt/nanobot-console/bots/<bot-id>/`, prepares isolated `data/`, `workspace/`, and `secrets/` directories, copies the bot secrets into that bot directory, renders `docker-compose.yml`, and runs:

```bash
docker compose -p nanobot_<bot-id> -f /opt/nanobot-console/bots/<bot-id>/docker-compose.yml up -d
```

Each bot Compose project uses the prebuilt `nanobot-enterprise-pilot:dev` image by default. The compose file mounts bot-local state into `/home/app/.nanobot`, bot workspace into `/workspace`, passes model, prompt, timezone, allowlist, proxy URL, and activity callback through environment variables, and exposes Telegram and provider secrets through Docker Compose secrets.

Inside the bot container, `/app/entrypoint.sh` runs `python /app/generate_config.py`. That script reads environment variables and secret files, writes `/home/app/.nanobot/config.json`, and enables the Telegram channel with the required allowlist. The entrypoint then starts the bot runtime:

```bash
nanobot gateway --config /home/app/.nanobot/config.json --workspace /workspace --port 18790
```

Stopping a bot runs the matching `docker compose ... down`. Runtime logs are read through `docker compose logs` for that bot's Compose project.

## Common Commands

```powershell
.\deployer\deploy.ps1
.\deployer\deploy.ps1 -DryRun
.\deployer\deploy.ps1 ak@192.168.155.66 -Port 22 -ConsolePort 8787
.\deployer\deploy.ps1 ak@192.168.155.66 -Domain console.example.com
.\deployer\deploy.ps1 ak@192.168.155.66 -IdentityFile C:\path\id_ed25519 -Yes
```

`-Yes` is for CI or other non-interactive runs. It disables SSH password prompts, requires key-based SSH login, and requires non-interactive `sudo`.

Useful options:

| Option | Meaning |
| --- | --- |
| `-DryRun` | Probe the server and stop before changes. |
| `-Yes` | Approve changes without prompts; for automation only. |
| `-Port PORT` | SSH port. |
| `-IdentityFile PATH` | SSH private key path. |
| `-RemoteRoot PATH` | Server install root. |
| `-ConsolePort PORT` | Console HTTP port. |
| `-Domain DOMAIN` | Publish the console as `https://DOMAIN/` using Caddy. |

## SSH Key Setup

Create a separate deploy key on the operator machine:

```powershell
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\nanobot_ed25519 -C "nanobot-deploy"
```

Add the public key to the server:

```powershell
type $env:USERPROFILE\.ssh\nanobot_ed25519.pub | ssh <user>@<vm-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
```

Check that SSH login works without a password:

```powershell
ssh -i $env:USERPROFILE\.ssh\nanobot_ed25519 <user>@<vm-ip>
```

Deploy with that key:

```powershell
.\deployer\deploy.ps1 <user>@<vm-ip> -IdentityFile $env:USERPROFILE\.ssh\nanobot_ed25519
```

## Requirements

Operator machine:

- PowerShell;
- OpenSSH `ssh`;
- OpenSSH `scp`;
- `tar`;
- network access to the server.

Target server:

- Ubuntu-compatible Linux;
- SSH server enabled;
- a user that can run `sudo`;
- outbound network access.

VM sizing:

- Minimum for a small test install: 1 vCPU, 1 GB RAM, 10 GB free disk.
- Recommended for normal use: 2 vCPU, 2 GB RAM, 20 GB free disk.
- Add more RAM and disk for many bots, large workspaces, verbose logs, or local/proxy services on the same VM.

Quick manual checks:

```powershell
ssh -V
scp
ssh <user>@<vm-ip>
ssh <user>@<vm-ip> "sudo true"
```

For `-Yes`, also verify key-based SSH and non-interactive sudo:

```powershell
ssh -o BatchMode=yes <user>@<vm-ip> "sudo -n true"
```

## Console Access

Without `-Domain`, the console is served as plain HTTP:

```text
http://<server>:8787/
```

Use plain HTTP only on a trusted network, VPN, firewall-restricted host, or SSH tunnel. If `ufw` is active on the VM, the deployer allows the console port. Provider firewalls/security groups may still need an inbound TCP rule for that port.

With `-Domain console.example.com`, the deployer binds the console backend to `127.0.0.1`, installs/configures Caddy when available, and publishes:

```text
https://console.example.com/
```

Point DNS at the server and allow inbound `80/tcp` and `443/tcp`.

In domain mode, if `ufw` is active on the VM, the deployer allows `80/tcp` and `443/tcp` and removes direct access to the console port.

## Create A Bot

Open the printed console URL and create a bot with:

- bot name;
- Telegram bot token;
- allowed Telegram user IDs;
- OpenRouter API key;
- OpenRouter model preset;
- optional timezone, proxy URL, and system prompt.

Click `Start`, then message the bot from an allowlisted Telegram account.

## Server Control

The deployer installs a helper on the server:

```bash
sudo /opt/nanobot-console/consolectl status
sudo /opt/nanobot-console/consolectl restart
sudo /opt/nanobot-console/consolectl logs
sudo /opt/nanobot-console/consolectl bot-logs <bot-id> 200
sudo /opt/nanobot-console/consolectl url
```

If Telegram is unreachable from the server, test it directly:

```powershell
ssh <user>@<vm-ip> 'curl -I --max-time 10 https://api.telegram.org'
```

If general internet works but Telegram is blocked, run a proxy/VPN on the server and set the bot `Proxy URL` in the UI.

## Security Notes

- Do not commit real secrets.
- Rotate any token that appears in chat, screenshots, terminals, or logs.
- Telegram allowlist is required before a bot can start.
- Secret values are written to server-side secret files and are not shown again by the API.
- Bot containers do not mount `docker.sock`.
- Bot containers run as a non-root app user.
- Bot state is isolated under `/opt/nanobot-console/bots/<bot-id>/`.

## Development Checks

```powershell
docker compose config
py -3 -m unittest tests.test_deployer tests.test_deploy_engine tests.test_console_ui tests.test_runtime_image tests.test_redact
```
