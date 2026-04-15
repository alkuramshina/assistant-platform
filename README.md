# Nanobot Enterprise Pilot

Репозиторий для пилота личного рабочего AI-ассистента на базе `nanobot`.
Цель пилота: поднять минимальный стек локально через Docker Compose, проверить канал Telegram и provider route через OpenRouter, сохранить состояние в named volumes и затем перенести тот же Compose-подход в Coolify.

## Source of Truth

Продуктовая и инфраструктурная правда живет в [`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md) и связанных документах в `docs/`.

`.planning/` используется только как рабочая память GSD. `.codex/` содержит локальные инструменты и skills. Эти каталоги не являются durable product docs и не должны заменять документы в `docs/`, `ops/runbooks/` и `ops/backup/`.

## Карта Репозитория

| Путь | Назначение |
|------|------------|
| [`docs/PROJECT_SUMMARY.md`](docs/PROJECT_SUMMARY.md) | Краткий продуктовый и инфраструктурный source of truth |
| [`docs/architecture.md`](docs/architecture.md) | Архитектура, среды, data flow, ограничения и границы фаз |
| [`docs/coolify-setup.md`](docs/coolify-setup.md) | Подготовленный путь деплоя через Coolify |
| [`ops/runbooks/first-deploy.md`](ops/runbooks/first-deploy.md) | Первый локальный запуск, smoke test и первичный backup |
| [`ops/runbooks/redeploy.md`](ops/runbooks/redeploy.md) | Redeploy, rollback и проверки перед рискованными изменениями |
| [`ops/backup/restore.md`](ops/backup/restore.md) | Restore application-data volumes из restic |
| [`docker/`](docker/) | Entrypoint и генерация runtime config для nanobot |
| [`docker-compose.yml`](docker-compose.yml) | Общий Compose-источник для local и remote deployment |
| [`.env.example`](.env.example) | Контракт конфигурации без реальных секретов |
| [`AGENTS.md`](AGENTS.md) | Короткие правила для AI-агентов в этом репозитории |

## Быстрый Локальный Контур

1. Создать локальный `.env` из `.env.example` и заполнить только локальные значения.
2. Проверить Compose:

   ```powershell
   docker compose config
   docker compose build nanobot
   docker compose up -d nanobot
   docker compose ps
   ```

3. Для полного smoke test отправить сообщение Telegram-боту с аккаунта из `CHANNEL_ALLOW_FROM`.
4. Проверить, что после `docker compose restart nanobot` named volumes `nanobot_data` и `nanobot_workspace` остаются на месте.

## Runtime Safety

Минимальная безопасная форма пилота:

- состояние nanobot хранится в named volumes `nanobot_data` и `nanobot_workspace`;
- `docker.sock` не монтируется в контейнер;
- широкие host bind mounts для workspace не используются;
- runtime по умолчанию запускается не от root через `APP_UID` и `APP_GID`;
- provider/channel keys поступают через Docker Compose secrets и `*_FILE`;
- реальные секреты не коммитятся в `.env.example`, docs или git history;
- публичный канал требует allowlist через `CHANNEL_ALLOW_FROM`;
- backup volumes считаются потенциально secret-bearing.

## Provider И Model Route

Локальный smoke path по умолчанию:

```text
DEFAULT_PROVIDER=openrouter
DEFAULT_MODEL=openrouter/free
CHANNEL_TYPE=telegram
```

`openrouter/free` является free-model router, поэтому фактическая backing model может меняться. Ответ бота о том, что он "GPT-4-Turbo" или другая модель, не является авторитетным источником. Проверять нужно generated config, значения provider/model и OpenRouter logs.

## Что Читать Дальше

- Архитектура и границы фаз: [`docs/architecture.md`](docs/architecture.md)
- Подготовка Coolify path: [`docs/coolify-setup.md`](docs/coolify-setup.md)
- Первый запуск: [`ops/runbooks/first-deploy.md`](ops/runbooks/first-deploy.md)
- Redeploy и rollback: [`ops/runbooks/redeploy.md`](ops/runbooks/redeploy.md)
- Restore application data: [`ops/backup/restore.md`](ops/backup/restore.md)

## Registry Publishing

Pilot images publish to private GHCR through GitHub Actions:

```text
REGISTRY_IMAGE=ghcr.io/OWNER/assistant-platform
IMAGE_TAG=sha-<git-sha>
```

Coolify should normally deploy immutable `sha-*` tags. GHCR pull access stays private and uses a read-only PAT, deploy token, or equivalent registry credential. Do not commit registry credentials or real secrets to repository files.
