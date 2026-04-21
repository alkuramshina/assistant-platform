---
phase: 10
name: Multi-Bot Isolation and Hardening
status: planned
created: "2026-04-21"
---

# Phase 10 Validation

## Automated

- Unit tests prove two bot records render to different project names, compose paths, data dirs, workspace dirs, and secret files.
- Unit tests prove stopping bot A runs `docker compose ... down` only for bot A's project.
- Unit tests audit rendered bot Compose for safety:
  - no `docker.sock`;
  - no `privileged`;
  - non-root user exists;
  - only expected per-bot bind mounts;
  - Docker secrets have restrictive metadata;
  - allowlist is required before deploy.
- Deployer tests cover:
  - default HTTP run prints explicit HTTP-only warning;
  - HTTPS/domain run writes/provisions reverse proxy config;
  - console service bind address is safe for the selected mode.
- Existing smoke-path tests still pass.

## Human UAT

- Deploy to Ubuntu VM.
- Create two bots with different Telegram tokens or at least different bot records/allowed users.
- Start both from UI.
- Send a message to bot A and bot B and confirm each responds.
- Stop bot A and confirm bot B stays running/responding.
- Confirm Activity/Runtime logs remain scoped to the selected bot.
- Confirm operator sees either:
  - HTTPS URL for configured domain; or
  - explicit HTTP-only warning if no domain is configured.

