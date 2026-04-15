# Redeploy

Use this when changing image tags, env vars, or nanobot configuration.

Read first:

- `docs/architecture.md`
- `docs/coolify-setup.md`
- `ops/backup/restore.md`

## Local redeploy

1. Validate Compose before changing the running service:

   ```sh
   docker compose config
   ```

2. Confirm the rendered config still uses named volumes `nanobot_data` and `nanobot_workspace`, has no `docker.sock` mount, and keeps the main service non-root.

3. Rebuild and restart:

   ```sh
   docker compose up -d --build nanobot
   ```

4. Check logs:

   ```sh
   docker compose logs -f nanobot
   ```

3. Optional smoke test through the configured channel.

## Registry-based redeploy

1. Build and push through GitHub Actions or locally:

   ```sh
   docker build -t ghcr.io/OWNER/assistant-platform:TAG .
   docker push ghcr.io/OWNER/assistant-platform:TAG
   ```

2. Set in Coolify:

   ```text
   REGISTRY_IMAGE=ghcr.io/OWNER/assistant-platform
   IMAGE_TAG=TAG
   ```

3. Trigger redeploy in Coolify.

## Before risky changes

Run a backup:

```sh
docker compose --profile ops run --rm backup
```

Treat this backup as secret-bearing application data. It can include generated config, memory, and workspace files.

## Rollback

1. Set `IMAGE_TAG` back to the previous known-good tag.
2. Redeploy.
3. If state migration or config generation corrupted data, stop the app and follow `ops/backup/restore.md`.

## Checks

- `docker compose config` renders without missing variables.
- `nanobot_data` and `nanobot_workspace` are still named volumes.
- No Docker socket mount was added.
- The main service still runs as non-root.
- `CHANNEL_ALLOW_FROM` remains configured for the selected channel.
