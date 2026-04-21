---
phase: 10
plan_id: 10-01
title: Multi-Bot Isolation and Hardening
status: planned
created: "2026-04-21"
requirements_addressed:
  - ISO-01
  - ISO-02
  - HARD-01
depends_on:
  - Phase 9 human UAT passed
---

# Plan 10-01: Multi-Bot Isolation and Hardening

## Objective

Make the prototype credible for two-bot operation on one server and add the first non-local hardening path: either HTTPS via reverse proxy or an explicit HTTP-only warning.

## Must Haves

- Two bots can be rendered, started, logged, and stopped independently.
- Stopping one bot does not target or stop the other bot's Compose project.
- Rendered bot Compose is audited for runtime safety constraints.
- Deployer behavior is honest about HTTP exposure and supports an HTTPS/domain path.
- Docs explain the safe deployment modes without adding long historical notes.

## Threat Model

| Threat | Severity | Mitigation |
|--------|----------|------------|
| Bot A reads Bot B state/secrets | High | per-bot paths, per-bot secret files, isolation tests |
| Stop/start action affects wrong bot | High | bot-scoped Compose project/file tests |
| Console exposed publicly over HTTP | High | HTTPS option or explicit HTTP-only warning |
| Bot container controls host Docker | High | no `docker.sock`, no privileged mode audit |
| Secrets leak through UI/runtime errors | High | keep redaction tests and do not return secret values |
| Single bot consumes host resources | Medium | document current limit and add resource-limit follow-up if not in scope |

## Tasks

### 1. Add Multi-Bot Isolation Tests

<read_first>

- `console/deploy.py`
- `tests/test_deploy_engine.py`
- `console/api.py`
- `tests/test_console_api.py`

</read_first>

<action>

Extend deployment tests so two bot records are deployed with distinct:

- bot IDs;
- Compose project names;
- compose file paths;
- data directories;
- workspace directories;
- secret files.

Add a stop-isolation test:

- start/deploy bot A and bot B;
- stop bot A;
- assert the captured command uses only bot A's project name and compose path;
- assert no command references bot B.

</action>

<acceptance_criteria>

- `tests/test_deploy_engine.py` contains a test named like `test_stopping_one_bot_targets_only_that_project`.
- Tests assert `nanobot_bot_one` and `nanobot_bot_two` or equivalent distinct project names.
- `py -3 -m unittest tests.test_deploy_engine` passes.

</acceptance_criteria>

### 2. Add Rendered Compose Safety Audit

<read_first>

- `console/deploy.py`
- `tests/test_deploy_engine.py`
- `docs/PROJECT_SUMMARY.md`

</read_first>

<action>

Add a focused test helper that audits rendered bot Compose text for Phase 10 safety constraints:

- does not contain `/var/run/docker.sock` or `docker.sock`;
- does not contain `privileged: true`;
- includes `user: "${APP_UID:-1000}:${APP_GID:-1000}"`;
- includes only the bot's own `data` and `workspace` mounts;
- includes Docker secrets for provider and channel;
- includes `uid`, `gid`, and restrictive secret mode;
- includes `CHANNEL_ALLOW_FROM`;
- does not include raw secret values.

If the rendered Compose lacks basic resource limits, document that as a Phase 10 residual risk or add conservative `mem_limit`/`cpus` values if they fit current deployment assumptions.

</action>

<acceptance_criteria>

- Safety audit test fails if `docker.sock`, privileged mode, missing non-root user, missing allowlist, or raw secret values appear.
- Existing deploy-engine tests still pass.
- Any resource-limit decision is captured in `docs/PROJECT_SUMMARY.md` or `deployer/README.md`.

</acceptance_criteria>

### 3. Add HTTPS / HTTP Warning Deployer Path

<read_first>

- `deployer/deploy.py`
- `deployer/remote/bootstrap.sh`
- `deployer/README.md`
- `README.md`
- `docs/PROJECT_SUMMARY.md`
- `tests/test_deployer.py`

</read_first>

<action>

Implement the smallest useful deployer behavior:

- add deployer config/flags for optional console domain, for example `--domain <domain>`;
- when no domain is configured, keep HTTP behavior but print a strong warning:
  - plain HTTP is for local/manual testing only;
  - do not expose it publicly;
  - use SSH tunnel, VPN, firewall, or the HTTPS/domain option.
- when a domain is configured:
  - render remote reverse-proxy config that proxies to the console backend on localhost;
  - bind console backend to `127.0.0.1` rather than `0.0.0.0`;
  - print `https://<domain>/` as the console URL.

Prefer a small Caddy-based implementation if it stays simple on Ubuntu. If Caddy installation is too broad for this phase, implement the config-generation path and explicit operator instructions, then mark actual package install as a residual risk/follow-up.

</action>

<acceptance_criteria>

- `deployer/deploy.py --dry-run` still works without a domain and reports an HTTP-only warning.
- Tests prove saved deployer config can store non-secret domain settings.
- Tests prove generated remote config/service uses `127.0.0.1` backend bind for HTTPS mode.
- Tests prove output URL is `https://<domain>/` when domain is configured.
- Existing deployer tests still pass.

</acceptance_criteria>

### 4. Add Console/UI Multi-Bot Diagnostics

<read_first>

- `console/api.py`
- `console/static/app.js`
- `console/static/index.html`
- `console/static/styles.css`
- `tests/test_console_ui.py`

</read_first>

<action>

Keep this minimal:

- ensure selected bot details show enough to distinguish bots safely:
  - bot ID;
  - status;
  - model;
  - timezone;
  - proxy URL;
  - secret storage status;
- ensure Activity and Runtime tabs remain scoped to the selected bot;
- if needed, add a small UI copy line that logs are for the selected bot only.

</action>

<acceptance_criteria>

- UI test confirms selected bot details include bot ID and status controls.
- UI test confirms Activity and Runtime endpoints include the selected bot ID.
- No browser storage for secrets.

</acceptance_criteria>

### 5. Update Docs And Human UAT

<read_first>

- `README.md`
- `deployer/README.md`
- `docs/PROJECT_SUMMARY.md`
- `.planning/phases/10-multi-bot-isolation-and-hardening/10-VALIDATION.md`

</read_first>

<action>

Update durable docs concisely:

- multi-bot done means;
- HTTP vs HTTPS behavior;
- how to run two-bot manual UAT;
- residual risks, especially resource limits if not implemented.

Create/update Phase 10 UAT notes with the exact human test:

- deploy;
- create two bots;
- start both;
- message both;
- stop one;
- confirm the other still responds;
- verify per-bot logs;
- verify HTTPS URL or HTTP warning.

</action>

<acceptance_criteria>

- README and deployer README mention Phase 10 safe exposure behavior.
- Human UAT file exists for Phase 10.
- Docs stay concise and do not reintroduce Coolify history.

</acceptance_criteria>

## Verification Commands

```powershell
py -3 -m unittest tests.test_deployer tests.test_deploy_engine tests.test_console_ui tests.test_runtime_image tests.test_redact
docker compose config
Select-String -Path console\deploy.py,deployer\remote\bootstrap.sh,deployer\deploy.py -Pattern "docker.sock|privileged: true|0.0.0.0|127.0.0.1|https://|HTTP-only"
```

## Human UAT

Follow `10-VALIDATION.md` after execution. The phase is not complete until one VM run proves two bots can coexist and one can be stopped without stopping the other.

