# Console

Local prototype UI and API for bot records, deployment actions, and activity logs.

Run:

```powershell
python -m console --db .local\console.db --host 127.0.0.1 --port 8787
```

Open:

```text
http://127.0.0.1:8787/
```

The UI can create bots, list statuses, start/stop rendered Compose projects, and show activity logs. It is local-prototype only and has no built-in auth yet.

Endpoints:

- `GET /health`
- `GET /api/bots`
- `POST /api/bots`
- `GET /api/bots/<id>`
- `POST /api/bots/<id>/start`
- `POST /api/bots/<id>/stop`
- `GET /api/bots/<id>/logs`
- `POST /api/bots/<id>/logs`

This API is local-prototype only. It stores secret references, not Telegram tokens or provider API keys.

Start/stop actions render per-bot Compose projects under the bot root. Each bot gets separate `data`, `workspace`, and `secrets` directories.
