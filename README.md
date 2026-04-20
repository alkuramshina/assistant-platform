# Assistant Platform

SSH-installed multi-bot console prototype for `nanobot`.

The customer provides a Linux server or VM. The installer connects over SSH, installs the console, and the console deploys isolated Telegram bot instances.

## Source Of Truth

- Product and architecture: [`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md)
- Agent working memory: `.planning/`
- Local agent tooling: `.codex/`

`.planning/` and `.codex/` are not product docs.

## Current Flow

```text
server/VM -> SSH install -> console UI -> create bot -> Telegram chat -> activity logs
```

## Prototype Must Prove

- install/update console on a customer server over SSH;
- create multiple bot instances from the UI;
- keep bot secrets outside git;
- isolate bot state and workspace per bot;
- require Telegram allowlist from first deploy;
- show request/response activity logs per bot.

## Installer

```powershell
py -3 installer\install.py user@server --dry-run
py -3 installer\install.py user@server
```

The installer prepares the server, starts the console service, and prints the UI URL. Telegram/provider credentials are entered in the UI.

Preflight on Windows:

```powershell
py -3 --version
ssh -V
scp
ssh user@server
ssh -o BatchMode=yes user@server "printf 'ssh=ok\n'"
```

The installer uses `BatchMode=yes`, so password prompts are disabled. Configure SSH key login first or pass `--identity-file`.

If BatchMode SSH fails:

```powershell
ssh-keygen -t ed25519
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh user@server "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys"
ssh -o BatchMode=yes user@server "printf 'ssh=ok\n'"
```

## Console API

```powershell
python -m console --db .local\console.db --bot-root .local\bots --secret-root .local\secrets
```

The API binds to `127.0.0.1` by default and stores secret references only.

## Useful Checks

```powershell
docker compose config
python -m py_compile installer\install.py
python -m unittest discover -s tests
rg -n "Coolify|coolify|GHCR|Azure OAuth" README.md docs AGENTS.md
```
