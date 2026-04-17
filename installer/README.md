# Installer

SSH installer for the prototype console.

Dry-run probe:

```powershell
python installer\install.py user@server --dry-run
```

Apply after reviewing planned host changes:

```powershell
python installer\install.py user@server
```

Non-interactive apply:

```powershell
python installer\install.py user@server --yes
```

Notes:

- target server should be Ubuntu-compatible Linux with SSH access;
- default install root is `/opt/nanobot-console`;
- missing Docker/Compose prerequisites require approval before installation;
- apply uploads the app, builds `nanobot-enterprise-pilot:dev`, installs a systemd service, starts the console, and prints the UI URL;
- Telegram/provider credentials are entered later in the console UI, not in the installer.
