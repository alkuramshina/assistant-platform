# AGENTS.md

## Repository Source of Truth

- Product and infrastructure truth lives in `docs/PROJECT_SUMMARY.md` and related files under `docs/`.
- `.planning/` is GSD working memory only. Use it for phase planning, but do not treat it as authoritative product documentation.
- `.codex/` is local tooling state and should not be treated as project source.
- If `.planning/` conflicts with `docs/`, follow `docs/` and update `.planning/` afterward.

## Documentation Policy

- Keep durable docs in `docs/`, `ops/runbooks/`, and `ops/backup/`.
- Keep `AGENTS.md` short: repo rules, source-of-truth pointers, verification commands, and safety constraints only.
- Do not store agent session logs, scratchpads, checkpoints, or long generated summaries in tracked project docs.
- Move important decisions discovered during agent work into durable docs before relying on them.

## Project Constraints

- Docker Compose is the shared source for local and remote deployment.
- Do not commit real secrets. Use `.env.example` for variable names and placeholder values only; runtime keys should enter containers through Docker Compose secrets or platform-managed secrets.
- Do not mount `docker.sock` into the nanobot container.
- Avoid unnecessary bind mounts and elevated container privileges.
- Keep nanobot runtime state in named volumes: `nanobot_data` and `nanobot_workspace`.
- Prefer OpenRouter free-model routing for the smoke-test path unless the user explicitly chooses paid API billing.

## Useful Checks

- Validate Compose syntax with `docker compose config`.
- Inspect the selected model/provider in `.env.example` before local smoke tests.
- For docs-only edits, verify links and source-of-truth references with `Select-String` or `rg`.
