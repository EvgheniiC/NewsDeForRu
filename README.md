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

**Статус:** сделано.

Сводка: типизированный `PipelineRunResponse`, блок последнего ручного `POST /pipeline/run`, сводка из `GET /health`, разделение сетевых ошибок и ответа с `ok: false` (см. `frontend/src/pages/FeedPage.tsx`, `frontend/src/lib/pipelineUi.ts`).

**Definition of Done:**

- [x] Пользователь видит метрики последнего ручного запуска пайплайна с главной страницы (режим сетки, панели).
- [x] Отображается сводка по последнему запуску из `/health`.
- [x] `npm run lint` и `npm run build` проходят.

---

### Пункт 4 — CI (непрерывная проверка)

**Статус:** сделано.

Workflow: [`.github/workflows/ci.yml`](.github/workflows/ci.yml) (push/PR на `main` и `master`). Статус последнего прогона — бейдж в шапке README и вкладка [Actions](https://github.com/EvgheniiC/NewsDeForRu/actions/workflows/ci.yml) в репозитории.

- Backend: Python 3.11, сервис PostgreSQL 16; `ruff check`, `mypy`, полный `pytest` (включая `test_migration_postgres` через `MIGRATION_TEST_ADMIN_URL`).
- Frontend: Node 20; `npm ci`, `npm run lint`, `npm run build`, `npm run test` (Vitest), `npm run test:e2e`.

**Definition of Done:**

- [x] CI запускается на push/PR и падает при нарушении lint/typecheck/tests.
- [x] В README кратко указано, где смотреть статус и как воспроизвести проверки локально.

---

### Пункт 5 — E2E / дымовые сценарии фронтенда

**Статус:** сделано.

Кратко: Playwright (`e2e/app-flow.spec.ts`), мок API через `page.route`, запуск `npm run test:e2e`.

**Definition of Done:**

- [x] Один конфигурируемый способ запуска E2E локально (`npm run test:e2e`).
- [x] Сценарии критического пути против выбранной стратегии API.

---

### Пункт 6 — Наблюдаемость бэкенда (логи и диагностика пайплайна)

**Статус:** сделано.

- Correlation: `run_id` в контексте (`app/monitoring/pipeline_run_context.py`), JSON-логи (`LOG_JSON=true`), plaintext (`LOG_PREFIX_RUN_ID_PLAIN`).
- Контекст ошибок по элементам: `item_error_details` (в т.ч. `cluster_id`, отпечаток URL).
- Опционально: `GET /metrics` (`PROMETHEUS_METRICS_ENABLED`), Sentry (`SENTRY_DSN`).

**Definition of Done:**

- [x] По логам прогона видна корреляция и числа, согласованные с API.
- [x] Секреты в логи не попадают (намеренно не записываем ключи и PII в stdout).

---

### Пункт 7 — Read-only «отладка происхождения» новости (опционально)

**Статус:** сделано (внутренний API).

- `GET /internal/provenance/by-raw/{raw_item_id}`, `GET /internal/provenance/by-processed/{processed_news_id}`.
- Заголовок `X-Internal-Api-Key` = `PROVENANCE_API_KEY`; без ключа ответ **404**.

**Definition of Done:**

- [x] Эндпоинты описаны здесь и в `backend/.env.example`; резюме — `/privacy`, шаблон: [`docs/privacy-EU-DE.md`](docs/privacy-EU-DE.md).
- [x] Не использовать как публичную поверхность.

## Frontend quick start

1. `cd frontend`
2. `npm install`
3. `npm run dev`
4. Открыть `http://127.0.0.1:5173`

## Основные API

- `GET /news` — опубликованная лента
- `GET /news/{id}` — карточка новости
- `GET /news/{id}` — поле `impact_presentation`: `multi` (три угла), `single` (один абзац в `impact_unified`) или `none` (без отдельного блока)
- `GET /news/{id}/impact?role=owner|tenant|buyer` — только если `impact_presentation` = `multi` (одна из трёх граней; иначе 404)
- `GET /moderation/queue` — очередь модерации
- `POST /moderation/{id}/action` — approve/reject
- `POST /pipeline/run` — запуск полного ingestion pipeline
- Внутреннее (см. `backend/.env.example`): `GET /internal/provenance/by-raw/{id}`, `GET /internal/provenance/by-processed/{id}` с заголовком `X-Internal-Api-Key`; `GET /metrics` при `PROMETHEUS_METRICS_ENABLED=true`

## Конфиденциальность (EU)

Страница приложения: `/privacy`. Шаблон для юриста и текстов GDPR: [`docs/privacy-EU-DE.md`](docs/privacy-EU-DE.md).

## Эксплуатация в продакшене

Краткий чеклист перед и во время эксплуатации (см. также [`backend/.env.example`](backend/.env.example)).

### Планировщик пайплайна

Встроенный APScheduler (`PIPELINE_SCHEDULER_ENABLED=true`) должен работать **только в одном процессе**. Если за приложением несколько воркеров uvicorn/gunicorn с одинаковым образом, включайте планировщик на одном инстансе (отдельный деплой/флаг окружения) **или** отключайте встроенный планировщик и запускайте прогон по cron/отдельному worker (вызов `POST /pipeline/run` или эквивалент). Иначе один и тот же интервал может выполняться параллельно на нескольких репликах и дублировать работу нагружая RSS и БД.

### Внутренний API происхождения (`/internal/provenance/*`)

- Задайте секрет **`PROVENANCE_API_KEY`** в хранилище секретов (не в git). Запросы с заголовком `X-Internal-Api-Key` должны быть только из доверенной сети (VPN, приватная подсеть, admin jump host). Если ключ пустой, маршруты отвечают **404** (фича выключена).
- Не выставляйте эти эндпоинты без защиты на публичный интернет как «ещё один REST».

### Метрики и ошибки

- **`GET /metrics`** (`PROMETHEUS_METRICS_ENABLED=true`): в проде не оставляйте без ограничения доступа при публичном ingress — закройте на уровне сетевого экрана, reverse-proxy (IP allowlist, mTLS, Basic auth) или отключите, если наблюдаемость не нужна.
- **`SENTRY_DSN`**: храните в секретах; пустое значение отключает отправку в Sentry.
- **Алерты (рекомендация):** по логам/метрикам отслеживайте `last_pipeline_ok` / неуспешные прогоны (см. `GET /health`), рост ошибок 5xx и длительность прогона пайплайна; при использовании Prometheus настройте правила на свои счётчики из `/metrics`.

## Engineering standards

- Python: strict typing, `ruff`, `mypy`, `pytest`
- Frontend: strict TypeScript, `eslint`, `vitest`, `prettier`
- All code comments must be in English
- Pre-commit checks are configured in `.pre-commit-config.yaml`

### Run checks

Локально те же шаги, что в CI (см. [workflow CI](.github/workflows/ci.yml)):

**Backend**

`cd backend`

`pip install -r requirements-dev.txt`

`ruff check app tests`

`mypy app`

`pytest`

Перед `pytest`: для проверки миграций на Postgres задайте `MIGRATION_TEST_ADMIN_URL`, как в разделе «Local PostgreSQL» выше.

**Frontend**

`cd frontend`

`npm ci`

`npm run lint`

`npm run build`

`npm run test`

`npx playwright install --with-deps chromium` (один раз на машину)

`npm run test:e2e`
