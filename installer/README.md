# Installer

SSH bootstrap installer for the prototype console.

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
- Phase 5 does not collect Telegram tokens or provider API keys;
- missing Docker/Compose prerequisites require approval before installation.
