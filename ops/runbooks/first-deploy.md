# First deploy

Goal: use the same `docker-compose.yml` locally and in Coolify, with no Docker socket mount and no host workspace bind mount.

## Local bootstrap

1. Create local env:

   ```sh
   cp .env.example .env
   ```

2. Fill in the minimum secrets in `.env`:

   - `DEFAULT_MODEL`
   - one provider key, for example `OPENROUTER_API_KEY`
   - one channel token, for example `TELEGRAM_TOKEN`
   - `CHANNEL_ALLOW_FROM`

3. Build and start:

   ```sh
   docker compose up -d --build nanobot
   ```

4. Check:

   ```sh
   docker compose ps
   docker compose logs -f nanobot
   docker volume ls | grep nanobot
   ```

## First backup

1. Fill backup env vars in `.env`.

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
