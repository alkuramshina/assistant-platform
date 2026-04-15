# First deploy

Goal: use the same `docker-compose.yml` locally and in Coolify, with no Docker socket mount and no host workspace bind mount.

## Local bootstrap

1. Create local env:

   ```sh
   cp .env.example .env
   ```

2. Fill in the minimum local values in `.env`.

   These defaults are already selected in `.env.example`:

   - `DEFAULT_PROVIDER=openrouter`
   - `DEFAULT_MODEL=openrouter/free`
   - `CHANNEL_TYPE=telegram`
   - `TELEGRAM_ENABLED=true`

   For the full Telegram/OpenRouter smoke test, fill real local values for:

   - `OPENROUTER_API_KEY`
   - `TELEGRAM_TOKEN`
   - `CHANNEL_ALLOW_FROM`

   Keep `.env` uncommitted. Do not put real secrets in `.env.example` or project docs.

   Secrets handling for this phase:

   - Non-secret defaults and allowlist values may live in local `.env`.
   - Provider and channel keys are passed to the container as Docker Compose secrets mounted under `/run/secrets`.
   - Compose sources those secrets from the local environment names `OPENROUTER_API_KEY`, `TELEGRAM_TOKEN`, and optional provider/channel key variables.
   - Backup credentials are also mounted as Compose secrets from `RESTIC_PASSWORD`, `BACKUP_ACCESS_KEY_ID`, and `BACKUP_SECRET_ACCESS_KEY`.
   - `docker/generate_config.py` reads `*_FILE` paths first, with direct env vars only as a compatibility fallback.
   - `CHANNEL_ALLOW_FROM` is required when an enabled channel has a token; startup fails fast if a public channel is enabled without an allowlist.

3. Run baseline checks:

   ```sh
   docker compose config
   docker compose build nanobot
   ```

4. Run the full local smoke test when Docker, network, and the local secrets above are available:

   ```sh
   docker compose up -d nanobot
   docker compose ps
   docker compose logs --tail=100 nanobot
   docker compose restart nanobot
   docker volume ls
   ```

   Send a Telegram message from the `CHANNEL_ALLOW_FROM` account and confirm the bot responds through OpenRouter.
   Confirm the named volumes `nanobot_data` and `nanobot_workspace` still exist after restart.

   If Docker, network, `.env`, or the required local values are unavailable, do not mark the full smoke test as passed; record it as blocked by the local environment.

## First backup

1. Fill backup secret values in local environment or `.env`:

   - `RESTIC_PASSWORD`
   - `BACKUP_ACCESS_KEY_ID`
   - `BACKUP_SECRET_ACCESS_KEY`

   `RESTIC_REPOSITORY` and `BACKUP_REGION` are non-secret configuration values.

2. Run:

   ```sh
   docker compose --profile ops run --rm backup
   ```

3. Inspect snapshots:

   ```sh
   docker compose --profile ops run --rm --entrypoint /bin/sh backup -c 'restic snapshots'
   ```

## Coolify import

1. Push the image to a private registry, GHCR by default.
2. In Coolify, create a Compose application from this repository.
3. Use the same `docker-compose.yml`.
4. Set env vars in Coolify instead of committing `.env`.
5. Use a private image name for `REGISTRY_IMAGE`, for example `ghcr.io/OWNER/assistant-platform`.
6. Keep both named volumes: `nanobot_data` and `nanobot_workspace`.
7. Do not add `/var/run/docker.sock` or host workspace bind mounts.

## Azure OAuth

Configure Azure OAuth for Coolify access, not inside the `nanobot` container. The app container stays focused on running the agent.

## Done

- The app starts from Compose.
- It runs as UID/GID `1000:1000` by default.
- State is in named volumes.
- Backups can read the same named volumes through the `ops` profile.
