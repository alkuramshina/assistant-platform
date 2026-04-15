# Architecture

Этот документ описывает логическую архитектуру Nanobot Enterprise Pilot. Краткий продуктовый и инфраструктурный source of truth остается в [`docs/PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md); здесь собраны детали runtime, сред, data flow и ограничений.

## Роль Документов

- [`docs/PROJECT_SUMMARY.md`](PROJECT_SUMMARY.md) фиксирует продуктовый контекст, выбранный стек и траекторию фаз.
- [`docs/architecture.md`](architecture.md) объясняет, как текущий стек работает технически.
- [`docs/coolify-setup.md`](coolify-setup.md) описывает подготовленный путь к Coolify.
- [`ops/runbooks/`](../ops/runbooks/) и [`ops/backup/`](../ops/backup/) содержат процедуры.
- `.planning/` и `.codex/` не являются source of truth для продукта.

## Среды

### Local

Локальная среда нужна для разработки и smoke test:

- Docker Desktop / Docker Engine;
- WSL2 на Windows, если используется Docker Desktop;
- тот же [`docker-compose.yml`](../docker-compose.yml), который позже используется для remote path;
- локальный `.env`, созданный из [`.env.example`](../.env.example);
- Docker Compose secrets, смонтированные в контейнер как файлы под `/run/secrets`.

### Remote Pilot

Remote pilot среда появляется в последующих фазах:

- отдельная Linux VM;
- Docker Engine;
- Coolify как pilot-level control plane;
- private registry image;
- те же named volumes `nanobot_data` и `nanobot_workspace`;
- отдельный application-data backup для nanobot volumes.

Phase 2 документирует целевую форму. Registry publishing относится к Phase 3, live Coolify UI validation к Phase 4, remote VM deployment к Phase 7.

## Service Model

Compose stack состоит из трех сервисов:

| Service | Назначение | Профиль |
|---------|------------|---------|
| `nanobot` | основной runtime ассистента | default |
| `backup` | ручной restic backup named volumes | `ops` |
| `restore` | ручной restic restore named volumes | `ops` |

`nanobot` собирается из [`Dockerfile`](../Dockerfile). Контейнер устанавливает `nanobot-ai`, копирует [`docker/entrypoint.sh`](../docker/entrypoint.sh) и [`docker/generate_config.py`](../docker/generate_config.py), затем запускается пользователем `app`.

## Data Flow

Основной smoke path:

```text
Telegram user
  -> Telegram Bot API
  -> nanobot channel
  -> generated config.json
  -> OpenRouter provider route
  -> selected/free backing model
  -> OpenRouter response
  -> nanobot
  -> Telegram Bot API
  -> Telegram user
```

Для локального пилота выбран:

```text
CHANNEL_TYPE=telegram
DEFAULT_PROVIDER=openrouter
DEFAULT_MODEL=openrouter/free
```

`openrouter/free` является free-model router. Фактическая backing model может меняться. Самоописание бота в ответе пользователю не считается авторитетным доказательством маршрута. Авторитетные источники: generated config, configured provider/model values и OpenRouter logs.

## Config Flow

Конфигурация проходит такой путь:

```text
.env.example / local .env / platform env
  -> docker-compose.yml environment
  -> Docker Compose secrets under /run/secrets
  -> docker/generate_config.py
  -> /home/app/.nanobot/config.json
  -> nanobot gateway
```

`docker/generate_config.py` сначала читает `*_FILE`, например `OPENROUTER_API_KEY_FILE` или `TELEGRAM_TOKEN_FILE`. Прямые env vars остаются compatibility fallback, но ключи в Compose передаются через secrets.

Если канал включен и у него есть token, `CHANNEL_ALLOW_FROM` обязателен. Для Telegram он превращается в `allowFrom` в generated `config.json`.

## Persistent State

Состояние не хранится в writable layer контейнера.

| Volume | Mount | Назначение |
|--------|-------|------------|
| `nanobot_data` | `/home/app/.nanobot` | config, runtime state, memory и служебные файлы nanobot |
| `nanobot_workspace` | `/workspace` | рабочие файлы ассистента |

Эти volumes используются локально и должны сохраниться в remote Compose/Coolify path.

## Runtime Constraints

Минимальная безопасная форма runtime:

- `docker.sock` не монтируется в `nanobot`;
- широкие host bind mounts для workspace не используются;
- `nanobot` работает через `user: "${APP_UID:-1000}:${APP_GID:-1000}"`;
- `Dockerfile` создает non-root пользователя `app`;
- `restart: unless-stopped` включен для `nanobot`;
- `init: true` включен в Compose;
- healthcheck проверяет наличие процесса `nanobot gateway`;
- provider/channel secrets поступают через Docker Compose secrets;
- публичный канал ограничивается `allowFrom` с первого дня.

Эти ограничения уже проверялись в Phase 1. Phase 8 остается отдельной фазой финального hardening review.

## Backup Boundary

Есть два разных backup слоя:

- Coolify control-plane backup: настройки и состояние самого Coolify.
- Nanobot application-data backup: `nanobot_data` и `nanobot_workspace`.

`ops` profile в Compose запускает restic backup/restore для application data. Эти backups считаются secret-bearing, потому что `nanobot_data` может содержать generated config и runtime state. Phase 6 должна валидировать backup/restore end to end и предпочитать explicit snapshot ID или tag вместо bare `latest`.

## Phase Boundaries

| Phase | Граница |
|-------|---------|
| Phase 2 | durable docs и runbooks для уже выбранного Compose path |
| Phase 3 | private registry publishing и image tag policy |
| Phase 4 | live Coolify import и UI validation |
| Phase 5 | pilot access constraints и allowlist verification |
| Phase 6 | backup/restore hardening и restore validation |
| Phase 7 | remote Linux VM deployment |
| Phase 8 | final pilot hardening review |
