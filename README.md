# newsForGermanyRU

Базовый монорепозиторий для старта приложения с разделением на:

- `frontend` — клиентская часть.
- `backend` — серверная часть на Python.

## Структура

- `frontend/`
- `backend/`
  - `app/`
  - `tests/`

## Быстрый старт (backend)

1. Перейдите в папку `backend`.
2. Создайте виртуальное окружение:
   - Windows PowerShell: `python -m venv .venv`
3. Активируйте окружение:
   - Windows PowerShell: `.\.venv\Scripts\Activate.ps1`
4. Установите зависимости:
   - `pip install -r requirements.txt`
5. Запустите сервер:
   - `uvicorn app.main:app --reload`

Проверка:

- Откройте `http://127.0.0.1:8000/health`
