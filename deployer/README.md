# Deployer

`deployer/deploy.py` installs or updates Nanobot Console on a Linux server over SSH.
It prepares the host, uploads the app, builds the bot image, starts the console service, and prints the UI URL.

The deployer does not ask for Telegram tokens or provider API keys. Those are entered later in the web console.

## Requirements

On the operator machine:

- Python launcher: `py -3 --version`
- OpenSSH client: `ssh -V`
- SCP: `scp`
- SSH key login to the target server

On the target server:

- Ubuntu-compatible Linux
- SSH server enabled
- target user can run `sudo`
- outbound network access
- access to Telegram API if you plan to run Telegram smoke tests

## First Run

From the repo root:

```powershell
py -3 deployer\deploy.py
```

The deployer asks for:

- SSH target, for example `<user>@<vm-ip>`
- SSH port, default `22`
- optional SSH identity file path
- remote install root, default `/opt/nanobot-console`
- console port, default `8787`

It then checks SSH, probes the server, asks for the remote Linux sudo password if needed, and asks for approval before changing host packages or services.

After a successful run it prints the console URL.

## Saved Settings

The first successful run writes `.deployer.json` in the repo root.
This file is gitignored and stores only non-secret deploy settings:

- SSH target
- SSH port
- identity file path, if provided
- remote root
- console port
- remembered host-change approval

It never stores the sudo password, Telegram token, provider key, or bot secrets.

Later runs usually need only:

```powershell
py -3 deployer\deploy.py
```

If the target user requires sudo password auth, the deployer asks for the password for that session only.

## Common Commands

Probe only, without changing the host:

```powershell
py -3 deployer\deploy.py --dry-run
```

Use explicit target:

```powershell
py -3 deployer\deploy.py <user>@<vm-ip>
```

Ignore saved settings for one run:

```powershell
py -3 deployer\deploy.py --reset-config
```

Do not save settings:

```powershell
py -3 deployer\deploy.py --no-save-config
```

Non-interactive apply:

```powershell
py -3 deployer\deploy.py <user>@<vm-ip> --yes
```

`--yes` never prompts. It requires SSH key login and non-interactive sudo on the target server.

## Flags

| Flag | Meaning |
|------|---------|
| `--dry-run` | Probe the host and print planned actions without applying changes. |
| `--yes` | Approve changes and fail instead of prompting. Useful for automation. |
| `--reset-config` | Ignore `.deployer.json` for this run. |
| `--no-save-config` | Do not write `.deployer.json`. |
| `--config PATH` | Use a different local deployer config file. |
| `--port PORT` | SSH port. |
| `--identity-file PATH` | SSH private key path. |
| `--remote-root PATH` | Install root on the target server. |
| `--console-port PORT` | HTTP port for the console UI. |

## Preflight Checks

Run these if the deployer cannot connect:

```powershell
py -3 --version
ssh -V
scp
ssh <user>@<vm-ip>
ssh -o BatchMode=yes <user>@<vm-ip> "printf 'ssh=ok\n'"
```

Set up SSH key login if BatchMode fails:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh <user>@<vm-ip> "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
ssh -o BatchMode=yes <user>@<vm-ip> "printf 'ssh=ok\n'"
```

Check sudo:

```powershell
ssh <user>@<vm-ip> "sudo true"
```

Check Telegram API reachability from the server:

```powershell
ssh <user>@<vm-ip> 'curl -I --max-time 10 https://api.telegram.org'
```

If general internet works but Telegram times out, configure a VPN/proxy on the server and use the console bot `Proxy URL` field, for example:

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

Use the web console to create bots, enter Telegram/provider secrets, start or stop bots, view activity, and inspect runtime logs.
