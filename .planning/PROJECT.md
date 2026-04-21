# Project

Working memory for GSD. Product truth lives in `README.md`.

## Current Direction

SSH-deployed multi-bot console for customer-provided Linux servers/VMs.

## Core Value

An operator can install a console over SSH, create Telegram nanobot instances in a UI, and inspect per-bot activity logs.

## Constraints

- Docker Compose is the per-bot runtime template.
- Bot containers do not mount `docker.sock`.
- Bot secrets stay outside git.
- Each bot has isolated data and workspace.
- Telegram allowlist is required from first deployment.
- Keep docs concise.

## Decisions

| Decision | Status |
|----------|--------|
| Drop Coolify from prototype path | Active |
| Use SSH deployer for customer server bootstrap | Active |
| Build a small console UI/API | Active |
| Support multiple isolated bot instances | Active |
| Log user requests and assistant responses per bot | Active |

## Current State

v1.0 MVP shipped on 2026-04-21.

Delivered:

- SSH/SCP deployer for installing and updating the console on a Linux VM.
- Remote bootstrap for Python, Docker, Compose, systemd service, optional Caddy HTTPS, and firewall adjustments.
- Console API and UI for creating, listing, starting, stopping, and inspecting Telegram Nanobot instances.
- Per-bot Docker Compose runtime with isolated data, workspace, secrets, logs, and project name.
- OpenRouter-backed model presets for the current UI.
- Runtime and Activity logs scoped to the selected bot.
- Human-verified Phase 9 smoke path and Phase 10 two-bot isolation.

## Next Milestone Goals

Define the next milestone from fresh requirements. Likely candidates:

- authentication/protection for the web console;
- provider selection beyond OpenRouter-only presets;
- stronger deploy diagnostics and recovery;
- production-grade domain/TLS guidance.

---

*Last updated: 2026-04-21 after v1.0 milestone.*
