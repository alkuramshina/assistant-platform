# Console

UI and API for bot records, deployment actions, and activity logs.

Run:

```powershell
python -m console --db .local\console.db --bot-root .local\bots --secret-root .local\secrets --host 127.0.0.1 --port 8787
```

Open:

```text
http://127.0.0.1:8787/
```

The UI can create bots, write server-side secret files, list statuses, start/stop rendered Compose projects, and show activity logs. Bind it locally or put it behind your own access control.

Endpoints:

- `GET /health`
- `GET /api/bots`
- `POST /api/bots`
- `GET /api/bots/<id>`
- `POST /api/bots/<id>/start`
- `POST /api/bots/<id>/stop`
- `GET /api/bots/<id>/logs`
- `POST /api/bots/<id>/logs`

The API stores secret references, not Telegram tokens or provider API keys. If secret values are submitted from the UI, they are written under the server-side secret root and are not returned in API responses.

Start/stop actions render per-bot Compose projects under the bot root. Each bot gets separate `data`, `workspace`, and `secrets` directories.
