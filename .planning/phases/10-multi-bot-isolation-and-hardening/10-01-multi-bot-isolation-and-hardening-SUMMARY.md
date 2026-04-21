# Phase 10 Summary

Implemented:

- Added stronger deployment-engine tests for two-bot isolation, one-bot stop targeting, and rendered Compose safety controls.
- Added deployer `--domain DOMAIN` support.
- Remote bootstrap now binds the console to `127.0.0.1` when a domain is configured and attempts Caddy HTTPS reverse proxy setup.
- Remote bootstrap prints an explicit HTTP warning when no domain is configured.
- UI logs section now states Activity and Runtime logs are scoped to the selected bot.
- README documents console exposure, `--domain`, and a concise two-bot manual check.

Verification:

- Unit tests passed.
- `docker compose config` passed.

Human UAT:

- Passed by human on 2026-04-21.
