# Installer

SSH installer for the prototype console.

Dry-run probe:

```powershell
py -3 installer\install.py user@server --dry-run
```

Interactive apply:

```powershell
py -3 installer\install.py
py -3 installer\install.py user@server
```

Non-interactive apply:

```powershell
py -3 installer\install.py user@server --yes
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
  - target user can run non-interactive `sudo`;
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

- without `--yes`, installer can ask for missing connection settings and offer retry prompts after SSH/sudo fixes;
- with `--yes`, installer never prompts and exits on failed preflight;
- installer uses `BatchMode=yes`, so SSH password prompts are disabled during install;
- SSH key login solves SSH authentication only; `sudo` must be non-interactive too. If needed, add a temporary sudoers file on the VM:

  ```bash
  echo 'user ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/nanobot-console-user
  sudo chmod 0440 /etc/sudoers.d/nanobot-console-user
  sudo -n true
  ```

- if BatchMode SSH fails, configure SSH key login first or use `--identity-file PATH_TO_KEY`;
- default install root is `/opt/nanobot-console`;
- missing Docker/Compose prerequisites require approval before installation;
- apply uploads the app, builds `nanobot-enterprise-pilot:dev`, installs a systemd service, starts the console, and prints the UI URL;
- Telegram/provider credentials are entered later in the console UI, not in the installer.
