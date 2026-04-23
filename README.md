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
5. `uvicorn app.main:app --reload`

Проверка:
- `GET http://127.0.0.1:8000/health`
- `POST http://127.0.0.1:8000/pipeline/run`

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
