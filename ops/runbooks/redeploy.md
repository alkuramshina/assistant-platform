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

5. Optional smoke test through the configured channel.

## Registry-based redeploy

1. Prefer publishing through GitHub Actions.

   The workflow publishes to GHCR on pushes to `main`, tags matching `v*`, and manual `workflow_dispatch`.
   For normal Coolify deployments, use an immutable tag such as `sha-<git-sha>`.
   For human release references, use a release tag such as `vX.Y.Z`.

2. Local build and push remains a fallback:

   ```sh
   docker build -t ghcr.io/OWNER/assistant-platform:sha-<git-sha> .
   docker push ghcr.io/OWNER/assistant-platform:sha-<git-sha>
   ```

3. Set in Coolify:

   ```text
   REGISTRY_IMAGE=ghcr.io/OWNER/assistant-platform
   IMAGE_TAG=sha-<git-sha>
   ```

4. Trigger redeploy in Coolify.

Do not use floating `main` as the normal Coolify deploy tag. It is convenient for CI visibility, but immutable `sha-*` tags make rollback and audit clearer.

For private GHCR packages, Coolify needs read-only package pull access through a PAT, deploy token, or equivalent registry credential. Do not commit registry credentials to `.env.example`, docs, or git history.

## Before risky changes

Run a backup:

```sh
docker compose --profile ops run --rm backup
```

Treat this backup as secret-bearing application data. It can include generated config, memory, and workspace files.

## Rollback

1. Set `IMAGE_TAG` back to the previous known-good immutable tag, for example `sha-<previous-git-sha>`.
2. Redeploy.
3. If state migration or config generation corrupted data, stop the app and follow `ops/backup/restore.md`.

## Checks

- `docker compose config` renders without missing variables.
- `nanobot_data` and `nanobot_workspace` are still named volumes.
- No Docker socket mount was added.
- The main service still runs as non-root.
- `CHANNEL_ALLOW_FROM` remains configured for the selected channel.
