# Roadmap

Source of truth: `docs/PROJECT_SUMMARY.md`.

## Phases

### Phase 4: Product Reframe and Console Architecture
**Goal**: Lock minimal architecture and implementation boundaries.
**Requirements**: REFRAME-01, ARCH-01, ARCH-02

### Phase 5: SSH Server Bootstrap Deployer
**Goal**: Install/update console on a Linux server over SSH.
**Requirements**: INST-01, INST-02, INST-03, INST-04

### Phase 6: Console API and Persistence
**Goal**: Store bots/config/log metadata and expose API.
**Requirements**: CONS-01, CONS-02, CONS-03

### Phase 7: Bot Template Deployment Engine
**Goal**: Render and run isolated per-bot Compose projects.
**Requirements**: BOT-01, BOT-02, BOT-03, BOT-04

### Phase 8: Minimal Console UI
**Goal**: Create/list/start/stop bots and view logs.
**Requirements**: UI-01, UI-02, UI-03

### Phase 9: Deployer-to-UI Telegram Smoke Path and Activity Logs
**Goal**: Prove Deployer-started console can deploy one bot that responds and logs request/response.
**Requirements**: SMOKE-00, SMOKE-01, LOG-01, LOG-02

### Phase 10: Multi-Bot Isolation and Hardening
**Goal**: Prove two bots coexist safely.
**Requirements**: ISO-01, ISO-02, HARD-01

## Current

Next: `/gsd-execute-phase 10`.
