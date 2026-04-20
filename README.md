# Assistant Platform

SSH-deployed multi-bot console for `nanobot`.

The customer provides a Linux server or VM. The deployer connects over SSH, installs or updates the console, and the console deploys isolated Telegram bot instances.

## Source Of Truth

- Product and architecture: [`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md)
- Agent working memory: `.planning/`
- Local agent tooling: `.codex/`

`.planning/` and `.codex/` are not product docs.

## Current Flow

```text
server/VM -> SSH deploy -> console UI -> create bot -> Telegram chat -> activity logs
```

## Current Goal

- deploy/update console on a customer server over SSH;
- create multiple bot instances from the UI;
- keep bot secrets outside git;
- isolate bot state and workspace per bot;
- require Telegram allowlist from first deploy;
- show request/response activity logs per bot.

## Deployer

```powershell
py -3 deployer\deploy.py user@server --dry-run
py -3 deployer\deploy.py
py -3 deployer\deploy.py user@server
py -3 deployer\deploy.py user@server --yes
```

The deployer prepares the server, starts the console service, and prints the UI URL. Telegram/provider credentials are entered in the UI.

Preflight on Windows:

```powershell
py -3 --version
ssh -V
scp
ssh user@server
ssh -o BatchMode=yes user@server "printf 'ssh=ok\n'"
ssh user@server "sudo -n true"
```

Without `--yes`, deployer can prompt for missing connection settings and retry after fixes. With `--yes`, it never prompts and exits on failed preflight.

The deployer uses `BatchMode=yes`, so SSH password prompts are disabled. SSH keys solve SSH login only. In interactive mode, deployer can ask for your remote sudo password for the deploy session; `--yes` requires non-interactive sudo.

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
py -3 -m unittest tests.test_deployer tests.test_console_ui
python -m unittest discover -s tests
rg -n "Coolify|coolify|GHCR|Azure OAuth" README.md docs AGENTS.md
```
