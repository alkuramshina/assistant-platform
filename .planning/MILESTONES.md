# Milestones

## v1.0 MVP (Shipped: 2026-04-21)

**Phases completed:** 7 phases, 8 plans
**Scope:** SSH-deployed multi-bot Nanobot Console for customer-provided Linux servers/VMs.

**Key accomplishments:**

- Reframed the product around an SSH-installed console and removed obsolete Coolify/backup prototype paths.
- Added a PowerShell SSH/SCP deployer that packages the app, probes the VM, applies approved host changes, and starts the console service.
- Built the console API, SQLite persistence, minimal UI, server-side secret handling, and per-bot activity/runtime logs.
- Added per-bot Docker Compose rendering with isolated data, workspace, secrets, and project names.
- Proved the Telegram smoke path on a VM, including proxied Telegram access and UI Activity request/response logging.
- Proved two-bot isolation and one-bot stop/start behavior through automated checks and human UAT.

**Verification:**

- Automated checks passed: unit suites and `docker compose config`.
- Human UAT passed for Phase 9 and Phase 10 on 2026-04-21.
- No separate milestone audit file was created before completion; phase verification and human UAT artifacts are the audit evidence for v1.0.

---
