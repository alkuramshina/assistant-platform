# Redeploy

Use this when changing image tags, env vars, or nanobot configuration.

## Local redeploy

1. Rebuild and restart:

   ```sh
   docker compose up -d --build nanobot
   ```

2. Check logs:

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

## Rollback

1. Set `IMAGE_TAG` back to the previous known-good tag.
2. Redeploy.
3. If state migration or config generation corrupted data, stop the app and follow `ops/backup/restore.md`.

## Checks

- `docker compose config` renders without missing variables.
- `nanobot_data` and `nanobot_workspace` are still named volumes.
- No Docker socket mount was added.
- The main service still runs as non-root.
