# Restore nanobot pilot

This restores the two application volumes from restic:

- `nanobot_data` mounted at `/home/app/.nanobot`
- `nanobot_workspace` mounted at `/workspace`

Coolify itself has a separate backup path. This document only covers application data.

## Security caveat

Backups of `nanobot_data` and `nanobot_workspace` may contain generated config, memory, workspace files, channel state, and other runtime data. Treat restic repositories as secret-bearing: encrypt them, restrict access, and do not paste real repository credentials into docs or tickets.

Phase 2 keeps the current restore mechanics documented. Phase 6 should validate backup/restore end to end and prefer an explicit snapshot ID or tag over a bare `latest` restore.

## Prerequisites

- Docker Engine and Docker Compose
- A checked out copy of this repository
- A valid `.env` with `RESTIC_REPOSITORY`, `RESTIC_PASSWORD`, `BACKUP_ACCESS_KEY_ID`, `BACKUP_SECRET_ACCESS_KEY`, and `BACKUP_REGION`
- The image tag that should run after restore

## Restore into empty volumes

1. Stop the app:

   ```sh
   docker compose stop nanobot
   ```

2. Create the named volumes if they do not exist yet:

   ```sh
   docker compose up --no-start nanobot
   ```

3. Restore a snapshot into the mounted volumes.

   Current pilot command:

   ```sh
   docker compose --profile ops run --rm \
     restore restore latest --target /
   ```

   `latest` is convenient for smoke testing but should not be treated as the final safe restore strategy. In Phase 6, prefer an explicit snapshot ID or a tagged snapshot selected after `restic snapshots`.

   The snapshots contain `/backup/nanobot_data` and `/backup/nanobot_workspace`.
   During restore these paths are backed by the same named volumes used by the app.
   The `restore` service mounts them read-write; the regular `backup` service mounts them read-only.

4. Start the app:

   ```sh
   docker compose up -d nanobot
   ```

5. Check logs:

   ```sh
   docker compose logs -f nanobot
   ```

## Restore over existing volumes

For a clean restore, create fresh volumes instead of overlaying files on top of old state.
If you must restore over existing data, stop `nanobot` first and make an extra snapshot before touching volumes.

Useful inspection commands:

```sh
docker compose --profile ops run --rm restore snapshots
docker compose --profile ops run --rm restore ls latest
```

For Phase 6 hardening, replace `latest` with the selected snapshot ID or tag in inspection and restore commands.

## Verification

- `nanobot` starts without config errors.
- The selected channel connects.
- Files under `/workspace` are present.
- Runtime files under `/home/app/.nanobot` are present.
