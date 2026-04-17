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
python installer\install.py user@server --dry-run
python installer\install.py user@server
```

Phase 5 installer does not collect Telegram tokens or provider API keys.

## Useful Checks

```powershell
docker compose config
python -m py_compile installer\install.py
rg -n "Coolify|coolify|GHCR|Azure OAuth" README.md docs AGENTS.md
```
