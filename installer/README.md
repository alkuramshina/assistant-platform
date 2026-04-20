# Installer

SSH installer for the prototype console.

Dry-run probe:

```powershell
py -3 installer\install.py user@server --dry-run
```

Apply after reviewing planned host changes:

```powershell
py -3 installer\install.py user@server
```

Non-interactive apply:

```powershell
py -3 installer\install.py user@server --yes
```

Notes:

- Windows operator machine needs Python 3 and OpenSSH:
  - `py -3 --version`
  - `ssh -V`
  - `scp`
- verify SSH manually first: `ssh user@server`;
- installer uses `BatchMode=yes`, so SSH password prompts are disabled during install;
- use key-based SSH login or `--identity-file PATH_TO_KEY`;
- target server should be Ubuntu-compatible Linux with SSH access;
- default install root is `/opt/nanobot-console`;
- missing Docker/Compose prerequisites require approval before installation;
- apply uploads the app, builds `nanobot-enterprise-pilot:dev`, installs a systemd service, starts the console, and prints the UI URL;
- Telegram/provider credentials are entered later in the console UI, not in the installer.
