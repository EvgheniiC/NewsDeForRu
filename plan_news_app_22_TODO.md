# plan_news_app_22 — ToDo и статус

Единый список: что уже сделано по надежности/наблюдаемости пайплайна и что остаётся по дорожной карте приложения (см. также `README.md`, раздел «План»).

---

## Сделано

### Backend: тесты, планировщик, мониторинг MVP, fallback

- [x] **Тесты (pytest)** — покрытие сервисов, API, health, миграций Postgres; добавлены: `test_pipeline_task`, `test_scheduler`, RSS retry, OpenAI network fallback.
- [x] **Планировщик** — APScheduler подключается в `lifespan` FastAPI при `PIPELINE_SCHEDULER_ENABLED=true`; интервал `PIPELINE_INTERVAL_MINUTES`; логирование результата прогона.
- [x] **Мониторинг MVP** — `GET /health`: проверка БД (`SELECT 1`), `last_pipeline_run_at`, `last_pipeline_ok`, флаг `pipeline_scheduler`; состояние последнего прогона в `app/monitoring/last_pipeline_run.py`.
- [x] **Fallback RSS** — несколько попыток на фид (`RSS_FEED_MAX_ATTEMPTS`), задержка между попытками (`RSS_FEED_RETRY_BASE_DELAY_SECONDS`), лог при окончательном сбое.
- [x] **Fallback LLM** — повтор запроса OpenAI при 429/5xx (`OPENAI_REQUEST_RETRIES`); при сетевых/транспортных ошибках — структурированный fallback; в пайплайне — `try/except` вокруг `process_news` + счётчик `item_errors`.
- [x] **Устойчивость фонового прогона** — `run_pipeline_task` при ошибке может вернуть `PipelineRunResponse` с `ok: false` (если `PIPELINE_TASK_SWALLOW_ERRORS=true`); ручной `POST /pipeline/run` с `swallow_errors=false` по-прежнему пробрасывает исключение.
- [x] **Схема ответа пайплайна** — `PipelineRunResponse`: `item_errors`, `ok`, `error` (см. `backend/app/schemas/news.py`).
- [x] **Логи** — итоговая строка после `PipelineService.run()`, предупреждения RSS, ошибки планировщика.
- [x] **Пример env** — новые переменные в `backend/.env.example`.

---

## Надо сделать

### Пункт 3 — UI: видимость пайплайна (React)

**Статус:** сделано.

- [x] Клиент: типизированный `PipelineRunResponse` (все поля, включая `item_errors`, `ok`, `error`).
- [x] Лента: индикатор загрузки + блок итогов последнего ручного `POST /pipeline/run`.
- [x] Отображение данных из `GET /health` (`last_pipeline_run_*`, статус БД).
- [x] Разделение сетевых ошибок и ответа с `ok: false`.
- [x] DoD: `npm run lint`, `npm run build`.

### Пункт 4 — CI

- [x] GitHub Actions (или аналог): backend `ruff`, `mypy`, `pytest`; frontend `lint`, `build`.
- [x] Политика для `test_migration_postgres` (сервис Postgres в CI или исключение).
- [x] Краткая ссылка в README на статус CI.

### Пункт 5 — E2E фронтенда

**Статус:** сделано.

- [x] **Playwright** + сценарий `e2e/app-flow.spec.ts`: лента → детали (карточка «Открыть») → модерация → Publish, проверка «Очередь пуста».
- [x] **API:** перехват `fetch` к `http://127.0.0.1:8000` через `page.route` (см. `e2e/fixtures/apiMock.ts`); CORS/OPTIONS для кросс-ориджин-запросов; **альтернатива** — поднять бэкенд и задать `VITE_API_BASE_URL` при сборке, без мока.
- [x] **Запуск:** `cd frontend && npm run test:e2e` (первый раз при необходимости `npx playwright install chromium`); `playwright.config` поднимает Vite; для UI: `npm run test:e2e:ui`.

### Пункт 6 — Наблюдаемость (углубление)

**Статус:** сделано.

- [x] Correlation / run id — `pipeline_run_context` + поле в JSON-логах; в plaintext — префикс `[run_id=...]` (`LOG_PREFIX_RUN_ID_PLAIN`, `LOG_JSON`).
- [x] Единый JSON на строку для прода (`LOG_JSON=true`).
- [x] Контекст `item_errors` — `PipelineItemErrorDetail` (в т.ч. `cluster_id`, `url_fingerprint`); расширение ответа API.
- [x] Опционально: `GET /metrics` (Prometheus, `PROMETHEUS_METRICS_ENABLED`), Sentry (`SENTRY_DSN`).

### Пункт 7 — Read-only «происхождение» новости

**Статус:** сделано.

- [x] Read-only API: `GET /internal/provenance/by-raw/{id}`, `GET /internal/provenance/by-processed/{id}` — цепочка raw → cluster → processed.
- [x] Защита: заголовок `X-Internal-Api-Key` = `PROVENANCE_API_KEY` (пусто → 404); пример — `README.md` / `backend/.env.example`.

---

## Примечания

- **Один процесс с планировщиком:** при нескольких репликах uvicorn/gunicorn включайте планировщик только на одном инстансе или вынесите прогон в cron/отдельный worker — иначе джобы могут дублироваться.
- **Фронтенд unit (Vitest):** `npm run test` — см. `src/lib/*.test.ts`.
- **EU / политика:** шаблон `docs/privacy-EU-DE.md`, страница `/privacy` на фронте; юридически согласовать перед публикацией.
- **Sklearn:** прототип метрики качества кластеров — `app/ml/cluster_quality_probe.py` (нужна разметка / gold-set для прод-оценки).