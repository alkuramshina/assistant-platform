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

It then copies the runtime files with `scp`, runs the remote bootstrap over `ssh`, asks for host-change approval, asks for the remote `sudo` password once if needed, starts the service, and prints the console URL.

Only the operator machine needs `ssh` and `scp`. Python runs on the server; the remote bootstrap installs `python3`, Docker Engine, and Docker Compose when needed and approved.

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

## Requirements

Operator machine:

- PowerShell;
- OpenSSH `ssh`;
- OpenSSH `scp`;
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

Use plain HTTP only on a trusted network, VPN, firewall-restricted host, or SSH tunnel.

With `-Domain console.example.com`, the deployer binds the console backend to `127.0.0.1`, installs/configures Caddy when available, and publishes:

```text
https://console.example.com/
```

Point DNS at the server and allow inbound `80/tcp` and `443/tcp`.

## Create A Bot

Open the printed console URL and create a bot with:

- bot name;
- Telegram bot token;
- allowed Telegram user IDs;
- provider API key;
- model preset;
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
