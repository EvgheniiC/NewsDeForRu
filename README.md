# newsForGermanyRU

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

- Backend: `cd backend && ruff check app tests && mypy app && pytest`
- Frontend: `cd frontend && npm run lint && npm run build`
