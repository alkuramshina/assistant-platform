# AGENTS.md

## Repository Source Of Truth

- Product and infrastructure truth lives in `docs/PROJECT_SUMMARY.md`.
- `.planning/` is GSD working memory only. Use it for phase planning, but do not treat it as authoritative product documentation.
- `.codex/` is local tooling state and should not be treated as project source.
- If `.planning/` conflicts with `docs/PROJECT_SUMMARY.md`, follow `docs/PROJECT_SUMMARY.md` and update `.planning/` afterward.

## Documentation Policy

- Keep durable product docs minimal. Prefer one concise document over many files.
- Keep `AGENTS.md` short: repo rules, source-of-truth pointers, verification commands, and safety constraints only.
- Do not store agent session logs, scratchpads, checkpoints, or long generated summaries in tracked project docs.
- Move important decisions discovered during agent work into durable docs before relying on them.

## Workflow Preferences

- Codex may run `git add` and `git commit` for its own scoped changes without asking for separate confirmation.
- Do not commit unrelated user changes or real secrets.

## Project Constraints

- Current product is an SSH-deployed multi-bot console for customer-provided Linux servers/VMs.
- Docker Compose is the per-bot runtime template.
- Do not commit real secrets. Use `.env.example` for variable names and placeholder values only; runtime keys should enter containers through Docker Compose secrets or platform-managed secrets.
- Do not mount `docker.sock` into bot containers.
- Avoid unnecessary bind mounts and elevated container privileges.
- Keep each bot's runtime state and workspace isolated.
- Require Telegram allowlist from first bot deployment.

## Useful Checks

- Validate Compose syntax with `docker compose config`.
- Inspect the selected model/provider in `.env.example` before local smoke tests.
- For docs-only edits, check stale historical terms with `rg -n "Coolify|coolify|GHCR|Azure OAuth" README.md docs AGENTS.md`.
