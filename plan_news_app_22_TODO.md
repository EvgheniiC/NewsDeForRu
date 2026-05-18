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

### Продакшен: VPS, домен, HTTPS (выполнено в базовом объёме)

- [x] **Один VPS (Hetzner Cloud)** — один сервер; без managed DB у провайдера: **PostgreSQL 16 в Docker** (`/opt/news-stack`), порт **5432** только на `127.0.0.1`.
- [x] **DNS** — записи **A** для `@`, **www**, **api** → IPv4 VPS; разделение фронта и API по хостам (**simplenewsapp.de** / **api.simplenewsapp.de**).
- [x] **Репозиторий на сервере** — `/opt/NewsDeForRu`, миграции Alembic на Postgres, **`backend/.env`** (в git не коммитится): `DATABASE_URL`, `CORS_ORIGINS` (HTTPS), `PUBLIC_APP_BASE_URL`, `APP_ENV=production`, секреты Telegram/OpenAI и т.д.
- [x] **API как служба** — **gunicorn** + **uvicorn worker**, **systemd** `news-api` (`enable` + `restart`), слушает **127.0.0.1:8000**; один воркер — планировщик пайплайна без дублирования.
- [x] **nginx** — статика SPA из **`/var/www/simplenewsapp/html`** (сборка Vite на сервере); **reverse proxy** на API для **api.simplenewsapp.de**; дефолтный сайт отключён.
- [x] **HTTPS** — **Let’s Encrypt** (certbot + плагин nginx), сертификаты для основного домена, **www** и **api**; редирект с HTTP на HTTPS.
- [x] **Фронт в проде** — `npm run build` с **`VITE_API_BASE_URL=https://api.simplenewsapp.de`**.
- [x] **Локальные runbook-файлы** (в `.gitignore`, не в репозитории): `prod-deployment-summary-ru.md`, `prod-architecture-ru.md`, `prod-logs-ru.md`, `prod-restart-ru.md`, `updateOnserver.md`, `deploy.md`.

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

### Пункт 8 — Публикация в Google Play / App Store (финальный этап)

**Статус:** не начато (текущий клиент — веб на React; магазины требуют нативный пакет или обёртку).

**«Скачать на всех устройствах»:** один **App Store** покрывает в основном экосистему **Apple** (iPhone / iPad / часть сценариев на Mac). Для **Android** нужен отдельно **Google Play** (или другой магазин, но Play — основной канал). То есть публичный охват «как у крупных медиа» — это **два релиза** (iOS + Android) либо одна **веб-обёртка**, которая затем публикуется в обоих магазинах по их правилам.

**Контекст:** в репозитории нет готового APK/AAB/IPA. Публичный прод (HTTPS, домены, CORS) **уже поднят** на VPS; дальше — выбор способа упаковки: **TWA / PWA в Google Play** (Bubblewrap, PWA Builder), **Capacitor/Cordova** (WebView + прод-сборка), либо отдельное нативное приложение.

**Кнопка «Читать в приложении» (Telegram):** сейчас backend строит HTTPS-URL вида `{PUBLIC_APP_BASE_URL}/news/{processed_id}` (см. `telegram_notifier.py`). После появления установленного клиента этот же URL должен **с помощью диплинков** открывать **конкретную новость внутри приложения**, а не только в браузере (через **Android App Links** + **iOS Universal Links** / Associated Domains для TWA/Capacitor, либо кастомная схема `myapp://` + fallback на https — проще для обёртки, хуже для UX и ревью).

- [x] **Прод-окружение (база):** стабильный публичный API (**`https://api.simplenewsapp.de`**), фронт по **HTTPS**, **CORS** на `https://simplenewsapp.de` / `www`, **`PUBLIC_APP_BASE_URL`**, секреты в **`.env` на сервере** (не в git); один воркер gunicorn + встроенный планировщик — ок для одного инстанса.
- [ ] **Прод-окружение (усиление):** вынести секреты в **Secrets Manager / нишевое хранилище** при росте требований; при появлении **нескольких реплик** API — вынести планировщик в один worker/cron или отключить `PIPELINE_SCHEDULER_ENABLED` на репликах; бэкапы БД по расписанию.
- [ ] **Стратегия упаковки:** зафиксировать вариант (TWA vs Capacitor vs native); для iOS и Android магазины могут отличаться по политике (минимальный функционал «оболочки», WebView-only и т.д.).
- [ ] **Диплинки под установленное приложение:** один канонический путь **`/news/:id`** на `PUBLIC_APP_BASE_URL`; на домене разместить **`/.well-known/assetlinks.json`** (Android) и **apple-app-site-association** (iOS); в проекте обёртки включить обработку входящих ссылок; проверить переход из Telegram → приложение на реальных устройствах.
- [ ] **Google Play:** аккаунт разработчика, подпись приложения (upload key), сборка **AAB**, карточка приложения (скриншоты, описание, категория), ссылка на политику конфиденциальности (согласовать `docs/privacy-EU-DE.md` / `/privacy`), при необходимости Data safety form.
- [ ] **App Store / TestFlight:** Apple Developer Program, сертификаты и профили, обёртка под iOS (Capacitor или актуальные правила для PWA), App Store Connect (метаданные, возрастной рейтинг, приватность), прохождение ревью.
- [ ] **Целостность продукта:** для веба — `PUBLIC_APP_BASE_URL=https://simplenewsapp.de` уже задаёт публичный origin; для магазинов при необходимости скорректировать диплинки под финальный клиент.

---

### Пост-деплой и эксплуатация (рекомендуется закрыть по мере созревания)

**Статус:** частично сделано / в бэклоге.

- [ ] **Файрвол:** включить **UFW** (или **Hetzner Cloud Firewall**) — **22** (SSH, лучше только свой IP), **`Nginx Full`** (80/443); не открывать **5432** и **8000** наружу.
- [ ] **Защита публичного API:** ограничить **`POST /pipeline/run`** (IP allowlist в nginx, секрет в заголовке, или только localhost + **cron** на сервере) — сейчас эндпоинт теоретически доступен с интернета через **api**-хост.
- [ ] **Бэкапы PostgreSQL:** периодический **`pg_dump`** (cron) + копия off-site; снапшоты диска Hetzner как дополнение, не замена логическим бэкапам.
- [ ] **Наблюдаемость в проде:** при желании **`LOG_JSON=true`**; при необходимости **Sentry** / метрики **`GET /metrics`** защитить или не включать публично (см. `README.md`).
- [ ] **Внутренние маршруты:** **`/internal/provenance/*`** и **`/metrics`** не выставлять «как есть» без сетевой изоляции или auth (см. `README.md`).
- [ ] **Обновления ОС:** после **`apt upgrade`** при запросе ядра — контролируемый **`reboot`**; проверить автозапуск **Docker**, **nginx**, **news-api**.
- [ ] **Let's Encrypt:** убедиться, что таймер **certbot** активен (`systemctl list-timers`); до истечения 90 дней сертификаты продлеваются автоматически.



подумай над форматом новостей срочно и чуть больше текста в новости?

---

## Примечания

- **Один процесс с планировщиком:** при нескольких репликах uvicorn/gunicorn включайте планировщик только на одном инстансе или вынесите прогон в cron/отдельный worker — иначе джобы могут дублироваться.
- **Фронтенд unit (Vitest):** `npm run test` — см. `src/lib/*.test.ts`.
- **EU / политика:** шаблон `docs/privacy-EU-DE.md`, страница `/privacy` на фронте; юридически согласовать перед публикацией.
- **Sklearn:** прототип метрики качества кластеров — `app/ml/cluster_quality_probe.py` (нужна разметка / gold-set для прод-оценки).