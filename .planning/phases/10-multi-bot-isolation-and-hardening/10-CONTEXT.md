---
phase: 10
name: Multi-Bot Isolation and Hardening
status: ready-for-planning
created: "2026-04-21"
source:
  - docs/PROJECT_SUMMARY.md
  - .planning/ROADMAP.md
  - .planning/REQUIREMENTS.md
---

# Phase 10 Context

## Goal

Prove Nanobot Console can safely run more than one bot on the same Linux server and close the most important runtime hardening gaps before the prototype is considered usable beyond a single smoke bot.

## Locked Scope

- Run two independently configured Telegram bots on one server.
- Keep each bot isolated by Compose project, filesystem paths, secrets, data, workspace, and logs.
- Stopping one bot must not stop or corrupt the other.
- Verify runtime safety constraints:
  - no `docker.sock` in bot containers;
  - no broad host bind mounts;
  - non-root bot container user;
  - Telegram allowlist required before start;
  - secrets stay in server-side files and are redacted from UI errors/logs.
- Add the HTTPS hardening path required by `docs/PROJECT_SUMMARY.md`:
  - plain HTTP remains acceptable only for local/manual testing;
  - deployer either configures a reverse proxy from operator-provided domain settings or prints an explicit HTTP-only warning.

## Current State

- Phase 9 passed human UAT: deployer starts console, UI starts one bot, Telegram replies, Activity logs request/response.
- Console binds to `0.0.0.0` in the systemd unit today and prints an HTTP URL.
- Bot deployment already uses per-bot directories under `/opt/nanobot-console/bots/<bot-id>/`.
- Bot Compose already avoids `docker.sock`, uses non-root user, per-bot data/workspace directories, per-bot secrets, and per-bot Compose project names.
- There is no automated multi-bot isolation acceptance test yet.
- There is no reverse-proxy/TLS deployer path yet.

## Constraints

- Keep implementation small and standard-library first.
- Do not add SaaS control planes, Coolify, Kubernetes, or multi-node orchestration.
- Do not commit real secrets.
- Do not break existing single-bot smoke path.
- Preserve existing deployer repeat-run behavior.

## Canonical References

- `docs/PROJECT_SUMMARY.md` - source of truth for product goal, Phase 10 HTTPS hardening, security rules, and done means.
- `.planning/REQUIREMENTS.md` - Phase 10 requirement IDs: `ISO-01`, `ISO-02`, `HARD-01`.
- `console/deploy.py` - per-bot Compose rendering and start/stop logic.
- `console/api.py` - bot lifecycle API and runtime log endpoint.
- `deployer/deploy.py` - operator-facing SSH deployer flow.
- `deployer/remote/bootstrap.sh` - remote host bootstrap, systemd unit, console URL output.
- `tests/test_deploy_engine.py` - current deployment isolation tests.
- `tests/test_deployer.py` - current deployer packaging and planning tests.

