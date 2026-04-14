# Nanobot Enterprise Pilot — Project Summary

Этот документ — продуктовый и инфраструктурный source of truth для пилота. Агентские рабочие артефакты вроде `.planning/` и локальные настройки вроде `.codex/` не являются источником правды; важные решения из них должны переноситься сюда или в соседние документы `docs/architecture.md`, `docs/coolify-setup.md` и runbooks.

## A. Контекст проекта

### A1. Цель
Собрать **fast enterprise pilot** личного рабочего AI-ассистента на базе **nanobot**.

Проект должен:
- запускаться **локально** для разработки и отладки;
- затем переноситься на **удалённую Linux VM** почти без изменений;
- иметь простой **control plane** для управления;
- быть пригодным для дальнейшего hardening под **corporate / on-prem** сценарии.

### A2. Целевая траектория
Рабочая траектория проекта:

1. **Локальный старт**
   - Docker Desktop
   - WSL2
   - локальный Docker Compose
   - быстрый smoke test

2. **Pilot deployment**
   - отдельная Linux VM
   - Coolify
   - private registry
   - backup
   - Azure OAuth

3. **Дальнейшее развитие**
   - внутренний pilot
   - enterprise hardening
   - возможный on-prem bundle

### A3. Что выбрано
Выбран следующий стек:

- **Runtime агента:** nanobot
- **Оркестрация:** Docker Compose
- **Консоль управления:** Coolify
- **SSO:** Azure OAuth
- **Registry:** private container registry
- **Backup:** внешний backup для volumes
- **Dev environment:** Docker + WSL
- **Pilot host:** отдельная Linux VM

### A4. Почему nanobot
Nanobot выбран как runtime для прототипа, потому что:
- лёгкий для старта;
- конфигурируемый;
- хорошо ложится в контейнер;
- подходит для pilot-level сценария;
- не заставляет сразу строить тяжёлую платформу.

### A5. Почему Coolify
Coolify выбран как pilot-level control plane, потому что:
- умеет работать с Docker Compose;
- имеет web UI;
- поддерживает Azure OAuth;
- подходит для single-host и multi-host сценариев через SSH;
- удобен для fast pilot.

Важно:
- Coolify подходит для **pilot / departmental platform**;
- но не рассматривается как окончательная “большая корпоративная платформа” без дополнительных слоёв.

---

## B. Архитектура решения

### B1. Логическая схема
Логика решения такая:

**Local dev machine**  
→ собирает и тестирует образ  
→ пушит образ в **private registry**  
→ Coolify деплоит стек на **remote VM**  
→ nanobot работает как отдельный сервис  
→ состояние хранится в persistent volumes  
→ backup job копирует volumes во внешний storage

### B2. Среды

#### Локальная среда
Используется для:
- сборки образа;
- отладки конфигурации;
- проверки канала;
- проверки провайдера моделей;
- проверки persistent volumes.

Состав:
- Docker Desktop
- WSL2
- локальный `docker-compose.yml`
- named volumes

#### Удалённая pilot-среда
Используется для:
- always-on запуска ассистента;
- демонстрации;
- работы с Coolify;
- проверки redeploy / backup / restore.

Состав:
- Linux VM
- Docker Engine
- Coolify
- Compose application
- private registry
- backup target
- Azure OAuth

### B3. Основные принципы
- **Docker Compose — единый источник правды**
- одна и та же структура должна работать локально и удалённо
- реальные секреты не коммитятся
- состояние агента хранится отдельно от контейнера
- deploy должен быть повторяемым
- внутренние сервисы не публикуются наружу без необходимости

---

## C. Ограничения и риски

### C1. Ограничения Docker Compose
Docker Compose подходит для пилота, но не решает сам по себе:
- зрелый RBAC;
- multi-node orchestration;
- HA;
- централизованный policy enforcement;
- полноценный enterprise secrets lifecycle.

### C2. Риски для agent runtime
Nanobot-подобный агент — это не просто web app.

Он потенциально работает с:
- файлами;
- shell-like действиями;
- внешними API;
- memory/state.

Поэтому уже на пилоте нужно:
- не давать лишние bind mounts;
- не монтировать `docker.sock`;
- не запускать контейнер с лишними привилегиями;
- использовать named volumes;
- ограничивать доступ к каналу через allowlist;
- делать отдельный backup данных приложения.

### C3. Что не делать в первой версии
Не включать сразу:
- Kubernetes
- multi-node
- локальные GPU-модели
- HA
- сложный observability stack
- полноценную multi-tenant enterprise platform

---

## D. Структура репозитория

Ожидаемая структура:

```text
nanobot-enterprise-pilot/
├─ docker-compose.yml
├─ .env.example
├─ .gitignore
├─ Dockerfile
├─ docker/
│  ├─ entrypoint.sh
│  └─ generate_config.py
├─ ops/
│  ├─ backup/
│  │  ├─ backup.sh
│  │  └─ restore.md
│  └─ runbooks/
│     ├─ first-deploy.md
│     └─ redeploy.md
├─ docs/
│  ├─ architecture.md
│  ├─ coolify-setup.md
│  └─ PROJECT_SUMMARY.md
└─ .github/
   └─ workflows/
      └─ build-and-push.yml
```

### D1. Назначение каталогов

#### `docker/`
Служебные файлы контейнера:
- `entrypoint.sh` — подготовка окружения и запуск nanobot
- `generate_config.py` — генерация `config.json` из env vars

#### `ops/backup/`
Файлы резервного копирования:
- `backup.sh` — выполняет backup volumes
- `restore.md` — описывает восстановление

#### `ops/runbooks/`
Операционные инструкции:
- первый деплой
- redeploy
- перенос на новый хост
- аварийное восстановление

#### `docs/`
Архитектурная и эксплуатационная документация.

#### `.github/workflows/`
CI/CD workflow для build-and-push образа в private registry.

---

## E. Compose stack

### E1. Минимальный состав сервисов
На первом этапе нужен минимум:
- `nanobot` — основной runtime агента
- `backup` — backup job, запускаемый вручную

### E2. Volumes
Нужны два named volume:
- `nanobot_data`
- `nanobot_workspace`

#### `nanobot_data`
Для:
- состояния агента
- конфигов
- памяти
- служебных файлов nanobot

#### `nanobot_workspace`
Для:
- рабочих файлов агента
- временных и рабочих данных

### E3. Environment variables
Переменные нужно делить на:
- обязательные;
- необязательные;
- секреты;
- значения по умолчанию.

---

## F. Registry, backup, SSO

### F1. Registry strategy
На старте рекомендуется:
- **GHCR** как private registry по умолчанию

Причины:
- легко встроить в GitHub Actions;
- удобно для private image;
- не требует сразу поднимать отдельный registry-хост.

Позже возможны:
- Harbor
- self-hosted registry
- корпоративный registry

### F2. Backup strategy
Backup делится на 2 уровня.

#### Backup уровня control plane
Backup самого Coolify.

Важно:
- это не backup данных приложения.

#### Backup уровня application data
Нужно отдельно бэкапить:
- `nanobot_data`
- `nanobot_workspace`
- при необходимости конфиги и связанные артефакты

Инструмент:
- `restic`

Хранилище:
- S3-compatible storage

### F3. SSO strategy
Для pilot-level корпоративного входа выбран:
- **Azure OAuth**

Это покрывает:
- базовый вход в Coolify;
- работу с корпоративными учётными записями на уровне пилота.

---

## G. Среда размещения

### G1. Как стартовать
Рекомендуемый порядок:
- сначала локальный запуск в Docker/WSL;
- затем перенос на отдельную VM.

### G2. Почему не только локально
Локальная машина не подходит как основная среда, потому что:
- не always-on;
- не изолирована от вашей рабочей среды;
- плохо подходит для демонстрации и дальнейшего корпоративного сценария.

### G3. VM для пилота
Для временного удалённого стенда допустим:
- бесплатный или почти бесплатный Linux VM

Один из кандидатов:
- Oracle Cloud Free Tier

Но free-tier VM — это только pilot / PoC, не production.

---

## H. Альтернативы текущему подходу

### H1. Альтернативы для прототипа
Если не использовать Coolify:
- Dokploy
- CapRover
- Podman + Quadlet

### H2. Альтернативы для корпоративного запуска
Если пилот пойдёт дальше:
- Portainer BE + Harbor
- Rancher + K3s + Harbor
- Nomad + Vault + Harbor
- OpenShift

### H3. Рекомендуемая эволюция
Сейчас:
- Coolify + Docker Compose

Если pilot удачен:
- переход к более enterprise-ready стеку

---

## I. План работ

### Phase 0 — зафиксировать scope

#### Цель
Сузить пилот до минимально жизнеспособного объёма.

#### Нужно определить
- 1 канал
- 1 LLM provider
- 1 локальная dev-среда
- 1 VM-цель
- 1 registry
- 1 backup target

#### Результат
Короткая зафиксированная конфигурация пилота.

---

### Phase 1 — локальный bootstrap

#### Цель
Сделать локальный стек запускаемым.

#### Задачи
- настроить Docker Desktop + WSL2;
- создать `.env` из `.env.example`;
- собрать образ;
- поднять `docker compose up -d`;
- проверить старт nanobot;
- проверить канал;
- проверить, что volumes сохраняют состояние.

#### Definition of done
- контейнер стартует;
- агент отвечает;
- состояние сохраняется.

---

### Phase 2 — привести репозиторий в порядок

#### Цель
Сделать репозиторий самодостаточным.

#### Задачи
- оформить структуру каталогов;
- поддерживать `docs/PROJECT_SUMMARY.md` как продуктовый source of truth;
- заполнить `docs/architecture.md`;
- дописать `ops/backup/restore.md`;
- создать `ops/runbooks/first-deploy.md`;
- создать `ops/runbooks/redeploy.md`;
- привести `.env.example` в финальный вид.

#### Definition of done
- репозиторий понятен без устных пояснений.

---

### Phase 3 — CI/CD и registry

#### Цель
Перевести стек на deploy из private registry.

#### Задачи
- добавить GitHub Actions workflow;
- настроить GHCR или другой registry;
- сделать первый push образа;
- зафиксировать naming/tagging policy.

#### Definition of done
- образ публикуется автоматически;
- образ можно использовать в Coolify.

---

### Phase 4 — поднять Coolify

#### Цель
Подготовить control plane пилота.

#### Задачи
- установить Coolify;
- подключить сервер;
- создать Project / Environment;
- импортировать Compose app;
- проверить env vars в UI.

#### Definition of done
- deploy запускается из Coolify.

---

### Phase 5 — подключить Azure OAuth

#### Цель
Включить базовый корпоративный вход.

#### Задачи
- создать App Registration в Azure / Entra;
- прописать redirect URI;
- настроить client id / client secret в Coolify;
- проверить логин.

#### Definition of done
- вход в Coolify работает через Azure OAuth.

---

### Phase 6 — backup и restore

#### Цель
Обеспечить переносимость и восстановление.

#### Задачи
- доделать `backup.sh`;
- настроить backup target;
- выполнить первый backup;
- оформить `restore.md`;
- протестировать восстановление.

#### Definition of done
- backup работает;
- restore описан и проверен.

---

### Phase 7 — перенос на удалённую VM

#### Цель
Перевести пилот на отдельный хост.

#### Задачи
- поднять Linux VM;
- установить Docker;
- развернуть или подключить Coolify;
- выполнить deploy;
- проверить работу агента;
- проверить volumes и backup.

#### Definition of done
- пилот работает вне локальной машины.

---

### Phase 8 — hardening пилота

#### Цель
Сделать решение инженерно аккуратным.

#### Задачи
- проверить отсутствие лишних bind mounts;
- убедиться, что нет `docker.sock`;
- убрать лишние права;
- проверить запуск не от root;
- проверить allowlist;
- зафиксировать runbooks.

#### Definition of done
- пилот пригоден для внутреннего показа.

---

## J. Backlog по приоритетам

### P0
- [ ] выбрать канал
- [ ] выбрать LLM provider
- [ ] собрать локальный образ
- [ ] поднять compose локально
- [ ] добиться ответа агента
- [ ] проверить persistent volumes
- [ ] оформить `.env.example`
- [ ] сохранить этот summary в репозиторий

### P1
- [ ] настроить GHCR/private registry
- [ ] добавить GitHub Actions workflow
- [ ] поднять Coolify
- [ ] включить Azure OAuth
- [ ] импортировать compose в Coolify
- [ ] настроить backup
- [ ] дописать `restore.md`
- [ ] оформить runbooks

### P2
- [ ] поднять удалённую VM
- [ ] выполнить перенос
- [ ] протестировать restore на новом хосте
- [ ] усилить работу с секретами
- [ ] оформить hardening checklist
- [ ] оценить enterprise-ready следующий шаг

---

## K. Правила ведения документации

В репозитории хранятся только устойчивые продуктовые и операционные документы:
- `docs/PROJECT_SUMMARY.md` — продуктовый и инфраструктурный source of truth;
- `docs/architecture.md` — архитектура, границы компонентов, среды и data flow;
- `docs/coolify-setup.md` — инструкция по pilot deploy через Coolify;
- `ops/runbooks/*.md` — операционные runbooks;
- `ops/backup/*.md` — backup/restore инструкции;
- `AGENTS.md` — короткие repo-level инструкции для AI-агентов;
- `.env.example` — контракт конфигурации без секретов.

Не являются source of truth и не должны попадать в обычный репозиторный history:
- `.planning/` — рабочая память GSD/агентов;
- `.codex/` — локальные skills, agents, настройки и служебные файлы конкретной машины;
- session logs, temporary summaries, checkpoints и agent scratchpads.

Если в `.planning/` появляется важное продуктовое решение, его нужно перенести в `docs/PROJECT_SUMMARY.md`, `docs/architecture.md`, `docs/coolify-setup.md` или runbook, а не коммитить `.planning/` как долгоживущий источник правды.

---

## L. Критерий успеха текущего этапа
Проект успешен, если:
- локально всё поднимается одной командой;
- nanobot отвечает в выбранном канале;
- состояние сохраняется в volumes;
- образ публикуется в private registry;
- тот же стек можно импортировать в Coolify;
- есть backup и понятный restore path.
