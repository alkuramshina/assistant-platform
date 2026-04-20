# Deployer

SSH deployer for Nanobot Console.

Dry-run probe:

```powershell
py -3 deployer\deploy.py user@server --dry-run
```

Interactive apply:

```powershell
py -3 deployer\deploy.py
py -3 deployer\deploy.py user@server
```

Non-interactive apply:

```powershell
py -3 deployer\deploy.py user@server --yes
```

After deploy, manage the console on the server:

```bash
sudo /opt/nanobot-console/consolectl restart
sudo /opt/nanobot-console/consolectl status
sudo /opt/nanobot-console/consolectl logs
sudo /opt/nanobot-console/consolectl bot-logs <bot-id>
sudo /opt/nanobot-console/consolectl url
```

Prerequisites:

- Windows operator machine:
  - Python 3 launcher: `py -3 --version`;
  - OpenSSH client: `ssh -V`;
  - OpenSSH copy tool: `scp`;
  - key-based SSH login to the server.
- Target server:
  - Ubuntu-compatible Linux;
  - SSH server enabled;
  - target user can run `sudo`;
  - outbound network access.

Preflight:

```powershell
py -3 --version
ssh -V
scp
ssh user@server
ssh -o BatchMode=yes user@server "printf 'ssh=ok\n'"
ssh user@server "sudo -n true"
```

Set up SSH key login if BatchMode fails:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh user@server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
ssh -o BatchMode=yes user@server "printf 'ssh=ok\n'"
```

Notes:

- without `--yes`, deployer can ask for missing connection settings and offer retry prompts after SSH/sudo fixes;
- with `--yes`, deployer never prompts and exits on failed preflight;
- deployer uses `BatchMode=yes`, so SSH password prompts are disabled during deploy;
- SSH key login solves SSH authentication only; it does not remove the remote sudo password prompt;
- interactive mode can ask for a remote sudo password for the deploy session and does not store it;
- `--yes` mode requires non-interactive sudo because there is no prompt;
- if BatchMode SSH fails, configure SSH key login first or use `--identity-file PATH_TO_KEY`;
- default deploy root is `/opt/nanobot-console`;
- missing Docker/Compose prerequisites require approval before package changes;
- apply uploads the app, builds `nanobot-enterprise-pilot:dev`, installs a systemd service, starts the console, and prints the UI URL;
- apply also installs `/opt/nanobot-console/consolectl` for restart/status/logs/url commands;
- Telegram/provider credentials are entered later in the console UI, not in the deployer.
