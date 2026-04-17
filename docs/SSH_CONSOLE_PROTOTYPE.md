# SSH-Installed Multi-Bot Console Prototype

This document is the current product direction after stopping the Coolify deployment track.

## Goal

Build a prototype that lets a customer bring their own Linux server or VM and install a small Nanobot control console over SSH.

The operator opens a simple UI, enters basic bot settings, clicks deploy, and gets a working Telegram-based nanobot instance. The same server can host multiple isolated bot instances.

## Pivot

Coolify and remote hosting are no longer required for the prototype. They added deployment complexity before proving the more important product loop:

```text
customer server -> SSH install -> create bot in UI -> talk through Telegram -> view activity logs
```

Coolify is deferred as an optional future backend.

## Target User Flow

1. Customer provides a Linux server or VM with SSH access.
2. Operator runs an installer:

   ```sh
   ./install.sh user@server
   ```

3. Installer checks the host, installs prerequisites when approved, and deploys the console.
4. Operator opens the console UI.
5. Operator creates a bot with:

   - bot name;
   - Telegram bot token;
   - allowed Telegram user IDs;
   - provider base URL;
   - provider API key;
   - model name;
   - optional system prompt.

6. Console deploys an isolated nanobot instance from a template.
7. User talks to the bot through Telegram.
8. Console shows activity logs with user requests and bot responses.

## Prototype Components

### SSH Installer

Responsibilities:

- verify SSH access;
- detect Linux OS and architecture;
- verify or install Docker Engine and Docker Compose;
- create `/opt/nanobot-console`;
- copy console assets and bot templates;
- create a systemd service for the console;
- print the UI URL and next steps.

### Console API

Responsibilities:

- create bot records;
- write per-bot secret files;
- render per-bot Compose templates;
- run `docker compose -p <project> up -d`;
- stop, start, and redeploy bot instances;
- collect status;
- expose activity logs to the UI.

### Console UI

Minimum screens:

- dashboard;
- bot list;
- create bot;
- bot details;
- activity logs;
- settings.

### Bot Instance

Each bot is an isolated deployment unit:

```text
/opt/nanobot-console/
  bots/
    <bot_id>/
      docker-compose.yml
      .env
      secrets/
        telegram_token
        provider_api_key
      data/
      workspace/
```

Each bot uses a unique Compose project name, separate storage, separate secrets, and explicit Telegram allowlist.

## Activity Log

The prototype must show at least:

- timestamp;
- bot ID/name;
- Telegram user ID;
- user request text;
- assistant response text;
- provider/model;
- status or error.

Preferred prototype approach: add structured request/response logging at the nanobot wrapper/runtime boundary. Container logs alone are not enough because the console needs queryable per-bot activity history.

## Infrastructure Defaults

- Customer host: Ubuntu LTS or compatible Linux server/VM.
- Install method: SSH.
- Runtime: Docker Engine + Docker Compose.
- Console persistence: SQLite for prototype.
- Bot persistence: per-bot volumes or directories managed by Compose.
- Secrets: server-side files with restrictive permissions.
- Channel: Telegram polling.
- Provider: configurable OpenAI-compatible provider URL/API key/model.

## Security Constraints

- Do not commit real secrets.
- Do not print secrets in logs or planning artifacts.
- Do not mount Docker socket into bot containers.
- Keep bot workspaces isolated per bot.
- Require Telegram allowlist from first deployment.
- Console may need host Docker access; bot containers must not.

## Prototype Definition Of Done

The prototype is successful when:

- installer can bootstrap a fresh Ubuntu server/VM over SSH;
- console UI opens;
- operator can create a first Telegram bot through the UI;
- console deploys the bot as an isolated Compose project;
- allowlisted Telegram user receives a response;
- UI shows request/response activity logs;
- operator can create a second bot on the same server without breaking the first;
- operator can stop/start each bot independently.
