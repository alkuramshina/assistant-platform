---
phase: 10
name: Multi-Bot Isolation and Hardening
status: complete
created: "2026-04-21"
---

# Phase 10 Research

## Findings

### Multi-Bot Isolation

Current architecture is already close:

- `DeploymentEngine.project_name()` derives a unique Compose project name per bot ID.
- `DeploymentEngine.paths()` derives per-bot root/data/workspace/secrets/compose paths.
- Compose renders only the bot's own data/workspace directories and secret files.
- Start/stop commands target the bot-specific Compose project and compose file.

The missing part is stronger acceptance coverage and user-visible diagnostics:

- a test that starts two bots and proves project names/paths/commands remain distinct;
- a test that stops one bot and proves the stop command targets only that bot's project;
- a helper/API surface to inspect effective runtime paths and safety constraints without reading files over SSH manually.

### Runtime Hardening

The existing bot Compose file should be treated as the hardening contract:

- no Docker socket mount;
- no privileged mode;
- non-root `user`;
- isolated per-bot bind mounts;
- Docker secrets with `uid`, `gid`, and restrictive mode;
- required `CHANNEL_ALLOW_FROM`;
- redacted deployment/runtime errors in UI.

Phase 10 should add an explicit automated audit over the rendered Compose YAML. This avoids relying on ad hoc visual review.

### HTTPS / Reverse Proxy

`README.md` says Phase 10 must harden non-local use: plain HTTP is only for local/manual testing; deployer should configure TLS from operator-provided domain settings or print an explicit HTTP-only warning.

Practical prototype path:

- keep console service itself on `127.0.0.1:<port>` when HTTPS is enabled;
- add an optional reverse proxy service/unit in front of it;
- ask for a domain only when the operator opts into HTTPS;
- otherwise print a clear warning that `http://<server>:<port>` is not for public exposure.

Caddy is a good fit for this phase because its official quick-start documents automatic HTTPS when a hostname points at the machine and ports 80/443 are reachable, and its `reverse_proxy` directive forwards traffic to a local backend while managing standard proxy headers. Docker's own docs confirm containers are unconstrained by default unless CPU/memory limits are set, so resource limits should be part of the hardening audit or follow-up if not implemented now.

Sources:

- Caddy reverse proxy quick-start: https://caddyserver.com/docs/quick-starts/reverse-proxy
- Caddy `reverse_proxy` directive: https://caddyserver.com/docs/caddyfile/directives/reverse_proxy
- Docker resource constraints: https://docs.docker.com/engine/containers/resource_constraints/

## Plan Implications

- Implement automated multi-bot isolation tests before changing deployer behavior.
- Add a small safety audit API/helper or test utility over rendered Compose.
- Add deployer flags/config for HTTPS:
  - `--domain <domain>`;
  - optional `--email <email>` if needed by chosen proxy flow;
  - default stays HTTP with explicit warning.
- Update README/deployer docs with HTTP vs HTTPS behavior.
- Keep manual UAT focused: create two bots, start both, stop one, verify the other responds, verify HTTPS/warning behavior.
