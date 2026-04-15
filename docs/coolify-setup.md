# Coolify Setup Path

Этот документ описывает подготовленный путь деплоя Nanobot Enterprise Pilot через Coolify.

Статус Phase 2: здесь фиксируется ожидаемая форма импорта и checklist. Live Coolify UI validation относится к Phase 4, после появления private registry image в Phase 3.

## Что Должно Быть Готово Перед Phase 4

- Private registry image, например через `REGISTRY_IMAGE` и `IMAGE_TAG`.
- Linux VM с Docker Engine и установленным Coolify.
- Доступ Coolify к private registry.
- Значения provider/channel/backup secrets.
- Понимание named volumes `nanobot_data` и `nanobot_workspace`.
- Прочитанные документы:
  - [`docs/architecture.md`](architecture.md)
  - [`ops/runbooks/first-deploy.md`](../ops/runbooks/first-deploy.md)
  - [`ops/runbooks/redeploy.md`](../ops/runbooks/redeploy.md)
  - [`ops/backup/restore.md`](../ops/backup/restore.md)

## Compose Import Expectations

Coolify должен использовать тот же [`docker-compose.yml`](../docker-compose.yml), который проверяется локально.

Сохраняются обязательные ограничения:

- не добавлять mount `/var/run/docker.sock`;
- не добавлять широкий host bind mount для workspace;
- сохранить named volumes `nanobot_data` и `nanobot_workspace`;
- сохранить non-root запуск через `APP_UID` и `APP_GID`;
- сохранить `restart: unless-stopped`;
- оставить healthcheck для `nanobot`;
- запускать backup/restore вручную через `ops` profile, а не как постоянно работающий сервис.

## Image Variables

В Coolify должны быть заданы значения:

```text
REGISTRY_IMAGE=ghcr.io/OWNER/assistant-platform
IMAGE_TAG=TAG
```

`REGISTRY_IMAGE` указывает на private registry image. `IMAGE_TAG` должен быть понятным deploy tag из Phase 3.

До Phase 3 локальный default может оставаться:

```text
REGISTRY_IMAGE=nanobot-enterprise-pilot
IMAGE_TAG=dev
```

## Environment And Secrets

Не коммитить `.env` и реальные ключи. В Coolify/platform UI значения делятся на два класса.

Non-secret env:

- `DEFAULT_PROVIDER`
- `DEFAULT_MODEL`
- `CHANNEL_TYPE`
- `TELEGRAM_ENABLED`
- `CHANNEL_ALLOW_FROM`
- `CHANNEL_GROUP_POLICY`
- `CHANNEL_GROUP_ALLOW_FROM`
- `NANOBOT_LOG_LEVEL`
- `NANOBOT_GATEWAY_PORT`
- `RESTIC_REPOSITORY`
- `BACKUP_REGION`
- `APP_UID`
- `APP_GID`
- `TZ`

Secret values:

- `OPENROUTER_API_KEY`
- `TELEGRAM_TOKEN`
- `OPENAI_API_KEY`, если OpenAI route будет включен позже;
- `ANTHROPIC_API_KEY`, если Anthropic route будет включен позже;
- `VLLM_API_KEY`, если vLLM route будет включен позже;
- `RESTIC_PASSWORD`;
- `BACKUP_ACCESS_KEY_ID`;
- `BACKUP_SECRET_ACCESS_KEY`.

Compose передает ключи как Docker Compose secrets и `*_FILE` values. Если Coolify не поддерживает ровно такую же secrets-форму для конкретного режима импорта, использовать platform-managed secret values и не хранить реальные значения в git.

## Access Checklist

Для Telegram smoke path `CHANNEL_ALLOW_FROM` должен быть задан с первого дня. Это список разрешенных Telegram account IDs через запятую.

Если `TELEGRAM_ENABLED=true` и есть `TELEGRAM_TOKEN`, generated `config.json` получает `allowFrom`. Без allowlist startup должен считаться небезопасным и неполным.

## Provider And Model Route

Default pilot route:

```text
DEFAULT_PROVIDER=openrouter
DEFAULT_MODEL=openrouter/free
```

`openrouter/free` может выбрать разную free backing model. Самоописание бота не доказывает фактический route. Проверять нужно generated config, configured provider/model values и OpenRouter logs.

## Phase 4 Validation Checklist

В Phase 4 UI-проверка должна подтвердить:

- Coolify импортирует тот же `docker-compose.yml`;
- `docker compose config`-эквивалент рендерится без missing variables;
- deployment стартует;
- `nanobot` health становится green;
- Telegram channel отвечает через выбранный provider/model path;
- volumes `nanobot_data` и `nanobot_workspace` существуют и не заменены bind mounts;
- logs позволяют увидеть выбранный provider/model route без раскрытия секретов;
- rollback через предыдущий `IMAGE_TAG` понятен оператору;
- backup/restore boundary не смешивается с Coolify control-plane backup.

## Связанные Runbooks

- Первый запуск и local smoke test: [`ops/runbooks/first-deploy.md`](../ops/runbooks/first-deploy.md)
- Redeploy и rollback: [`ops/runbooks/redeploy.md`](../ops/runbooks/redeploy.md)
- Restore application data: [`ops/backup/restore.md`](../ops/backup/restore.md)
