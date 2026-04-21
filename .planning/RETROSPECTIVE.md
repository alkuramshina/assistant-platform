# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 - MVP

**Shipped:** 2026-04-21
**Phases:** 7 | **Plans:** 8 | **Sessions:** multiple focused implementation/UAT sessions

### What Was Built

- SSH/SCP deployer that installs and updates a Nanobot Console on a Linux VM.
- Console API, SQLite persistence, and minimal UI for creating and controlling Telegram bots.
- Per-bot Docker Compose runtime with isolated data, workspace, secrets, and logs.
- Runtime and Activity logs scoped to the selected bot.
- Domain/HTTP-only deployment modes with basic firewall handling.

### What Worked

- Real VM UAT exposed the right deployment problems: sudo prompts, SCP directory upload behavior, provider firewall rules, Caddy/ACME behavior, and Telegram proxy requirements.
- Keeping durable product docs in `README.md` made repeated doc cleanup much easier.
- Per-bot bind-mounted data/workspace directories fit Nanobot's own memory/runtime model.

### What Was Inefficient

- The original Python deployer path created confusion once the PowerShell deployer became the real operator entrypoint.
- Provider configuration drifted: UI presets were OpenRouter, while runtime initially labeled the provider as `vllm`.
- Phase 9 had a missing closure summary, which made GSD progress under-report completion until corrected.

### Patterns Established

- Operator machine should only need PowerShell/OpenSSH/tar; Python work happens on the server.
- Interactive deploy and CI deploy are separate modes.
- Deployment uploads should be packaged and filtered, not raw recursive SCP of the repo.
- Human UAT status belongs in phase UAT files; product truth belongs in `README.md`.

### Key Lessons

1. Remote deployers need to make network/firewall mode explicit: HTTP-only and domain/TLS are different exposure policies.
2. Runtime config should use the provider Nanobot docs expect; compatibility hacks make failures harder to debug.
3. Bot memory persistence depends on preserving the Nanobot workspace and config/data directories, so isolation must be path-based and per-bot.

### Cost Observations

- Model mix: not tracked.
- Sessions: not tracked.
- Notable: small, direct UAT loops found higher-value issues than more speculative planning would have.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Sessions | Phases | Key Change |
|-----------|----------|--------|------------|
| v1.0 | multiple | 7 | Shifted from hosted-control-plane ideas to SSH-installed customer VM console. |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | unit suites plus VM UAT | focused on deploy/runtime/UI flows | stdlib console API and deploy primitives |

### Top Lessons

1. Keep the operator workflow brutally explicit: what runs locally, what runs remotely, and when passwords are expected.
2. Treat external network dependencies as first-class deployment configuration, especially Telegram and ACME.

