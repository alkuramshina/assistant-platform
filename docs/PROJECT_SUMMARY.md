# Project Summary

## Goal

Build a console for deploying multiple isolated `nanobot` Telegram assistants on a customer-provided Linux server or VM.

The operator should not need Coolify or a managed hosting platform. They should run an SSH deployer, open a small UI, enter bot/provider settings, and get a working bot.

## User Flow

```text
customer server -> SSH deployer -> console UI -> create bot -> Telegram -> activity logs
```

1. Operator provides SSH access to a Linux server.
2. Deployer checks prerequisites and installs or updates the console.
3. Operator opens the local console UI.
4. Operator creates a bot with:
   - bot name;
   - Telegram token;
   - allowed Telegram user IDs;
   - provider base URL;
   - provider API key;
   - model name;
   - optional system prompt.
5. Console deploys an isolated bot instance.
6. User talks to the bot in Telegram.
7. Console shows user requests, assistant responses, status, and errors.

## Architecture

### SSH Deployer

Installs or updates the console on the target server.

- verify SSH access;
- detect Linux OS and architecture;
- verify Docker Engine and Docker Compose;
- request approval before installing missing prerequisites;
- create `/opt/nanobot-console`;
- install console service files and bot templates;
- upload the console app and build the local bot image;
- start the console service;
- print the console URL.

Phase 5 deployer scope is host bootstrap only. It does not collect Telegram tokens or provider API keys.

### Console

Small server-side web app with API, UI, and SQLite persistence.

- create/list/start/stop bot instances;
- persist bot records and activity logs in SQLite;
- render per-bot Compose files;
- write secret files with restrictive permissions;
- run Compose projects for each bot;
- collect bot status and activity logs.
- keep raw Telegram/provider secrets out of API responses and logs.

Phase 6 console scope is local JSON API and SQLite persistence only. It binds to `127.0.0.1` by default and stores secret references, not secret values.

Phase 8 console scope adds a minimal local UI for creating bots, listing statuses, starting/stopping bot Compose projects, and reading activity logs. It does not add authentication or prove the Telegram smoke path.

Phase 9 must prove the real deployer-to-UI path on a Linux server or VM. The operator should not manually create console directories, copy app files, create secret folders, or run `python -m console`; the deployer prepares the host, starts the console, and prints the URL. The operator then uses the UI to enter bot/provider settings, start one bot, complete a Telegram smoke test, and see request/response logs.

Phase 10 must harden the system for non-local use: add an HTTPS reverse proxy path, keep plain HTTP limited to local/manual testing, and make the deployer either configure TLS from operator-provided domain settings or print an explicit HTTP-only warning.

### Bot Instance

Each bot is isolated:

```text
/opt/nanobot-console/bots/<bot_id>/
  docker-compose.yml
  secrets/
  data/
  workspace/
```

Each bot has its own Compose project name, secrets, data, workspace, Telegram allowlist, provider config, and logs.

Phase 7 deployment scope renders per-bot Compose files and starts/stops them from the console host. Bot containers do not receive host Docker control.

### Activity Logs

Record the minimum useful audit trail:

- timestamp;
- bot ID/name;
- Telegram user ID;
- user request;
- assistant response;
- provider/model;
- status or error.

## Security Rules

- Do not commit real secrets.
- Do not print secrets in logs.
- Bot containers must not mount `docker.sock`.
- Bot containers must not get broad host bind mounts.
- Telegram allowlist is required from first deployment.
- Store provider and Telegram keys as server-side secret files.
- Treat activity logs as sensitive user content.
- Require explicit operator approval before the deployer changes host packages or services.
- Do not expose the console over plain HTTP outside local/manual testing.

## Roadmap

| Phase | Goal |
|-------|------|
| 4 | Product reframe and console architecture |
| 5 | SSH server bootstrap deployer |
| 6 | Console API and persistence |
| 7 | Bot template deployment engine |
| 8 | Minimal console UI |
| 9 | Deployer-to-UI Telegram smoke path and activity logs |
| 10 | Multi-bot isolation, HTTPS, and hardening |

## Out Of Scope

- Coolify;
- Kubernetes;
- hosted SaaS control plane;
- multi-node orchestration;
- enterprise RBAC;
- SSO;
- full backup product.

## Done Means

- deployer can bootstrap a fresh Ubuntu server over SSH;
- console UI opens;
- operator can deploy a first Telegram bot;
- allowlisted Telegram user gets a response;
- UI shows request/response logs;
- operator can deploy a second bot on the same server;
- bots can be stopped and started independently.
