# Project Summary

## Goal

Build a prototype console for deploying multiple isolated `nanobot` Telegram assistants on a customer-provided Linux server or VM.

The operator should not need Coolify or a managed hosting platform. They should run an SSH installer, open a small UI, enter bot/provider settings, and get a working bot.

## User Flow

```text
customer server -> SSH installer -> console UI -> create bot -> Telegram -> activity logs
```

1. Operator provides SSH access to a Linux server.
2. Installer checks prerequisites and installs the console.
3. Operator opens the console UI.
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

### SSH Installer

Installs or updates the console on the target server.

- verify SSH access;
- detect Linux OS and architecture;
- verify Docker Engine and Docker Compose;
- request approval before installing missing prerequisites;
- create `/opt/nanobot-console`;
- install console service files and bot templates;
- print the console URL.

### Console

Small server-side web app with API, UI, and SQLite persistence.

- create/list/start/stop bot instances;
- render per-bot Compose files;
- write secret files with restrictive permissions;
- run Compose projects for each bot;
- collect bot status and activity logs.
- keep raw Telegram/provider secrets out of API responses and logs.

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
- Require explicit operator approval before the installer changes host packages or services.

## Roadmap

| Phase | Goal |
|-------|------|
| 4 | Product reframe and console architecture |
| 5 | SSH server bootstrap installer |
| 6 | Console API and persistence |
| 7 | Bot template deployment engine |
| 8 | Minimal console UI |
| 9 | Telegram smoke path and activity logs |
| 10 | Multi-bot isolation and prototype hardening |

## Out Of Scope

- Coolify;
- Kubernetes;
- hosted SaaS control plane;
- multi-node orchestration;
- enterprise RBAC;
- SSO;
- full backup product.

## Done Means

- installer can bootstrap a fresh Ubuntu server over SSH;
- console UI opens;
- operator can deploy a first Telegram bot;
- allowlisted Telegram user gets a response;
- UI shows request/response logs;
- operator can deploy a second bot on the same server;
- bots can be stopped and started independently.
