# Console API

Local prototype backend for bot records and activity logs.

Run:

```powershell
python -m console --db .local\console.db --host 127.0.0.1 --port 8787
```

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
