# newsForGermanyRU

[![CI](https://github.com/EvgheniiC/NewsDeForRu/actions/workflows/ci.yml/badge.svg)](https://github.com/EvgheniiC/NewsDeForRu/actions/workflows/ci.yml)

Приложение для понятной русскоязычной ленты новостей из Германии:
`RSS -> нормализация -> фильтрация -> дедупликация -> AI-обработка -> публикация`.

## Текущая структура

- `backend/` — FastAPI + pipeline + scheduler + тесты
- `frontend/` — React (TypeScript) лента, детали, модерация

## Backend quick start

1. `cd backend`
2. `python -m venv .venv`
3. `.\.venv\Scripts\Activate.ps1`
4. `pip install -r requirements.txt`
5. `alembic upgrade head`
6. `uvicorn app.main:app --reload`

Проверка:
- `GET http://127.0.0.1:8000/health`
- `POST http://127.0.0.1:8000/pipeline/run`

### Database migrations

- Apply migrations: `cd backend && alembic upgrade head`
- Create migration: `cd backend && alembic revision -m "your_message"`
- Auto-generate diff: `cd backend && alembic revision --autogenerate -m "your_message"`
- Rollback one step: `cd backend && alembic downgrade -1`

### Local PostgreSQL (Docker)

- Start DB: `docker compose up -d postgres`
- Stop DB: `docker compose down`
- Backend DB URL: `postgresql+psycopg://news:news@127.0.0.1:55432/newsdb`
- Run migration on PostgreSQL:
  - PowerShell: `$env:DATABASE_URL="postgresql+psycopg://news:news@127.0.0.1:55432/newsdb"; cd backend; alembic upgrade head`
- Run integration migration test:
  - PowerShell: `$env:MIGRATION_TEST_ADMIN_URL="postgresql+psycopg://news:news@127.0.0.1:55432/postgres"; cd backend; pytest tests/test_migration_postgres.py`

### Plan status: пункт 2 (DB schema raw/processed/clustered)

Status: done locally.

Definition of Done checklist:
- [x] PostgreSQL schema for `raw_news_items`, `processed_news`, `news_clusters`, `cluster_items`, `sources` is defined in Alembic migration.
- [x] `alembic upgrade head` succeeds on a clean PostgreSQL database.
- [x] Integration migration test exists: `backend/tests/test_migration_postgres.py`.
- [x] End-to-end pipeline path works on PostgreSQL: `raw -> clustered -> processed`.
- [x] Backend quality checks pass locally: `ruff`, `mypy`, `pytest`.

## План: следующие пункты

Актуальный чеклист «сделано / осталось»: [`plan_news_app_22_TODO.md`](plan_news_app_22_TODO.md).

### Пункт 3 — UI: видимость пайплайна (React)

**Статус:** запланировано.

**Цель:** после действий пользователя и фоновых прогонов было понятно, что сделал пайплайн (цифры, успех/ошибка, время последнего запуска).

**Задачи:**

- Расширить API-клиент: `POST /pipeline/run` должен возвращать типизированный `PipelineRunResponse` (поля как в `backend/app/schemas/news.py`: `fetched`, `feeds_failed`, `filtered_out`, `clustered`, `processed`, `published`, `needs_review`, `item_errors`, `ok`, `error`).
- На странице ленты: индикатор загрузки на время запроса; после ответа — компактный блок с итогами последнего ручного запуска (числа + явное сообщение при `ok: false` / `error`).
- Добавить запрос `GET /health` (или отдельный хук): показывать в UI `last_pipeline_run_at`, `last_pipeline_ok`, статус БД (например в шапке или collapsible «Статус системы»).
- Обработать сетевые и HTTP-ошибки так, чтобы не терять контекст (отдельно от «пайплайн вернул ok: false»).

**Definition of Done:**

- [ ] Пользователь видит метрики последнего ручного запуска пайплайна с главной страницы.
- [ ] Отображается сводка по последнему запуску из `/health` (хотя бы время и успех/неуспех).
- [ ] `npm run lint` и `npm run build` проходят.

---

### Пункт 4 — CI (непрерывная проверка)

**Статус:** сделано.

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (push/PR на `main` и `master`). Статус последнего прогона — бейдж в шапке README и вкладка [Actions](https://github.com/EvgheniiC/NewsDeForRu/actions/workflows/ci.yml) в репозитории.

- Backend: Python 3.11, сервис PostgreSQL 16; `ruff check`, `mypy`, полный `pytest` (включая `test_migration_postgres` через `MIGRATION_TEST_ADMIN_URL`).
- Frontend: Node 20; `npm ci`, `npm run lint`, `npm run build`.

**Definition of Done:**

- [x] CI запускается на push/PR и падает при нарушении lint/typecheck/tests.
- [x] В README кратко указано, где смотреть статус и как воспроизвести проверки локально.

---

### Пункт 5 — E2E / дымовые сценарии фронтенда

**Статус:** запланировано.

**Цель:** регрессия критического пути «лента → детали → модерация» ловится автоматически.

**Задачи:**

- Выбрать инструмент (например Playwright) и добавить зависимости/скрипт в `frontend`.
- Поднять тестовый бэкенд или мок API (минимум: мок `fetch` / test server) — зафиксировать в документации стратегию.
- Сценарии (минимум): открытие ленты; переход на `/news/:id` (с мок-данными); открытие `/moderation` и отображение очереди.
- Опционально: прогон E2E в CI на пуш (с учётом времени и флакинесса).

**Definition of Done:**

- [ ] Один конфигурируемый способ запуска E2E локально (`npm run test:e2e` или аналог).
- [ ] Три сценария выше зелёные против выбранной стратегии API.

---

### Пункт 6 — Наблюдаемость бэкенда (логи и диагностика пайплайна)

**Статус:** запланировано.

**Цель:** проще разбирать сбои ingestion, LLM и публикации без ручного дебага по одному breakpoint.

**Задачи:**

- Структурировать логи ключевых шагов пайплайна (уровень, этап, correlation/run id при необходимости, счётчики из `PipelineRunResponse`).
- Единообразно логировать ошибки по элементам (`item_errors`) с достаточным контекстом (id/url источника без секретов).
- Опционально: метрики (Prometheus/OpenTelemetry) или хотя бы расширение `/health` под «последняя ошибка пайплайна» (без утечки PII).

**Definition of Done:**

- [ ] По логам одного прогона видно прохождение этапов и итоговые числа, согласованные с ответом API.
- [ ] Нет дублирования секретов в логах.

---

### Пункт 7 — Read-only «отладка происхождения» новости (опционально)

**Статус:** запланировано (низкий приоритет).

**Цель:** из UI или API видно связь raw → cluster → processed для одной публикации.

**Задачи:**

- Спроектировать read-only эндпоинты (например для внутренней/админ-роли): список последних raw, деталь кластера, цепочка для `processed_news.id`.
- Страница или секция во фронте только для разработки/админа (фичефлаг или отдельный роут).
- Ограничить доступ (токен, IP, env-only) — по политике проекта.

**Definition of Done:**

- [ ] Документированный API + минимальный UI или `curl`-примеры.
- [ ] Явно отмечено, что это не публичная поверхность для конечных пользователей.

## Frontend quick start

1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Открыть `http://127.0.0.1:5173`

## Основные API

- `GET /news` — опубликованная лента
- `GET /news/{id}` — карточка новости
- `GET /news/{id}/impact?role=owner|tenant|buyer` — персонализированный блок
- `GET /moderation/queue` — очередь модерации
- `POST /moderation/{id}/action` — approve/reject
- `POST /pipeline/run` — запуск полного ingestion pipeline

## Engineering standards

- Python: strict typing, `ruff`, `mypy`, `pytest`
- Frontend: strict TypeScript, `eslint`, `prettier`
- All code comments must be in English
- Pre-commit checks are configured in `.pre-commit-config.yaml`

### Run checks

Локально те же шаги, что в CI (см. [workflow CI](.github/workflows/ci.yml)):

- Backend: `cd backend && pip install -r requirements-dev.txt && ruff check app tests && mypy app && pytest`
- Frontend: `cd frontend && npm ci && npm run lint && npm run build`

Интеграционный тест миграций (`tests/test_migration_postgres.py`) в CI идёт против сервиса Postgres; локально задайте `MIGRATION_TEST_ADMIN_URL` как в разделе «Local PostgreSQL» выше.
