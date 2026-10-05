# TODO: активация открытых источников

Состояние на 10.08.2026.

> Рабочий технический список, не юридическая консультация. Перед production
> необходимо повторно проверить актуальные лицензии и условия каждого источника.

## Уже активировано

- [x] Destatis RSS — `destatis`
- [x] European Commission Press Corner RSS — `ec_press_corner`
- [x] Destatis GENESIS — curated tables + API token
- [x] Eurostat — `prc_hicp_midx,une_rt_m,demo_pjan`
- [x] GovData — 3 starter packages
- [x] data.europa.eu — 3 starter datasets

Production-конфигурация (подтверждено на сервере 10.08.2026):

```env
RSS_ENABLED_SOURCE_KEYS=destatis,ec_press_corner
GENESIS_DATASET_CODES=61111-0002,61111-0004,12411-0001,13211-0006,81000-0007
EUROSTAT_DATASET_CODES=prc_hicp_midx,une_rt_m,demo_pjan
GOVDATA_PACKAGE_IDS=durchschnittsalter-der-bevolkerung-in-deutschland-ab-1871,bevolkerung-in-deutschland-nach-altersgruppen-ab-1871,preisentwicklung-der-jahre-1991-bis-2018
DATA_EUROPA_DATASET_IDS=https-www-regionalstatistik-de-genesisws-downloader-00-tables-aig-08-2_00,https-www-regionalstatistik-de-genesisws-downloader-00-tables-ai-n-07_00,05211a5d-6d0e-463b-8cc5-4c5bb51a3623
DATA_EUROPA_MAX_DISTRIBUTIONS_PER_DATASET=1
```

## Общие обязательные условия

- [ ] Применить актуальные Alembic-миграции: `alembic upgrade head`.
- [ ] Убедиться, что публикация без подтверждённой лицензии блокируется.
- [ ] Хранить источник, оригинальный URL, лицензию, дату получения и ревизию.
- [ ] Показывать уведомление о неофициальном переводе и AI-суммаризации.
- [ ] Не импортировать фотографии, видео, логотипы и сторонние приложения.
- [ ] Обрабатывать изменения, удаления и исправления исходных материалов.
- [ ] Ограничивать частоту запросов и использовать кэш.
- [ ] Проверить атрибуцию в приложении, API, Telegram, Push и Share.
- [ ] Провести тестовый запуск на staging до включения production scheduler.

---

## 1. Destatis GENESIS-Online

Статус: источник активирован (токен + дедуп + bypass relevance).
Базовый набор из 2 таблиц проверен; расширенный curated-набор ниже.

### Что нужно сделать

- [x] Зарегистрировать бесплатную учётную запись GENESIS-Online.
- [x] Создать API-токен.
- [x] Сохранить токен только в production secret management.
- [x] Начать с небольшого списка таблиц:
  - `61111-0002` — индекс потребительских цен, Германия, месяцы;
  - `12411-0001` — население Германии по датам.
- [x] Проверить размер и структуру ответов обеих таблиц на staging.
- [x] Убедиться, что повторный запуск не создаёт дубликаты.
- [x] Проверить качество русской AI-интерпретации числовых данных.
- [x] Добавить curated-расширение на prod:
  - `61111-0004` — ИПЦ по категориям расходов (годы);
  - `13211-0006` — уровень безработицы (месяцы);
  - `81000-0007` — зарплаты brutto/netto и соцвзносы (годы).
- [ ] Не добавлять `61111-0006` (месячные категории), пока не проверен размер ответа.
- [ ] При необходимости подтвердить качество AI-карточек для новых кодов.

### Production-конфигурация

```env
GENESIS_API_TOKEN=<REAL_SECRET_TOKEN>
# Baseline (проверено):
# GENESIS_DATASET_CODES=61111-0002,12411-0001
# Curated next (добавлять после проверки каждой новой таблицы):
GENESIS_DATASET_CODES=61111-0002,61111-0004,12411-0001,13211-0006,81000-0007
```

### Критерии готовности

- [ ] Токен не попадает в Git, логи и API-ответы.
- [ ] Ошибка одной таблицы не останавливает остальные источники.
- [ ] Публикуются только новые ревизии данных.
- [ ] В интерфейсе указаны Destatis, DL-DE-BY-2.0 и дата получения.

---

## 2. Eurostat

Статус: клиент с allowlist-фильтрами реализован. **Prod env выставлен**
(10.08.2026). Осталось подтвердить smoke/качество карточек, если ещё не смотрели.

### Что нужно реализовать

- [x] Добавить фильтры API минимум по `geo=DE`.
- [x] Ограничить период последними доступными месяцами или годами.
- [x] Ограничить показатели и единицы измерения для каждого dataset.
- [x] Добавить максимальный размер ответа до загрузки JSON в память.
- [x] Сохранить последовательное выполнение запросов без параллельного extraction.
- [x] Добавить source-specific настройки фильтров вместо одного списка кодов.
- [x] Добавить тесты фильтров, лимита размера, таймаутов и повторных ревизий.
- [x] Задеплоить backend и выставить `EUROSTAT_DATASET_CODES` на prod.
- [ ] Прогнать / подтвердить pipeline: raw-item без дубликатов, качество AI-карточек.

### Allowlisted наборы

- `prc_hicp_midx` — HICP индекс, Германия, all-items (`CP00`), последние 6 месяцев;
- `une_rt_m` — безработица %, Германия, SA / TOTAL, последние 6 месяцев;
- `demo_pjan` — население на 1 января, Германия, TOTAL, последние 5 лет.

Неизвестные коды fail-closed (skipped + `feeds_failed`).

### Production-конфигурация

```env
EUROSTAT_DATASET_CODES=prc_hicp_midx,une_rt_m,demo_pjan
EUROSTAT_MAX_RESPONSE_BYTES=500000
```

### Критерии готовности

- [x] Каждый запрос ограничен Германией и необходимым периодом.
- [x] Ответ имеет контролируемый размер.
- [ ] Исключения конкретного dataset проверены до публикации.
- [ ] В интерфейсе показаны Eurostat, ссылка на dataset и disclaimer перевода.

---

## 3. GovData / data.gov.de

Статус: MVP реализован (CKAN allowlist). GovData — каталог; правообладатель
и лицензия берутся у исходного publisher/resource.

### Что нужно реализовать

- [x] Создать CKAN importer с rate limit и лимитом размера (allowlist packages).
- [x] Загружать данные у исходного поставщика, а не считать GovData владельцем.
- [x] Проверять лицензию каждой `distribution/resource`, а не только dataset.
- [x] Разрешать автоматически только:
  - CC0;
  - CC BY;
  - DL-DE Zero 2.0;
  - DL-DE BY 2.0.
- [x] Блокировать NC, ND и ShareAlike; unknown → `rights_verified=False` → NEEDS_REVIEW.
- [x] Очередь ручной проверки неизвестных лицензий (существующая модерация LICENCE).
- [x] Хранить publisher, dataset URI, resource URI и license URI (в raw fields/summary).
- [x] Добавить тесты allowlist и обязательной блокировки unknown/NC.
- [x] Задеплоить и выставить `GOVDATA_PACKAGE_IDS` на prod.
- [ ] Подтвердить pipeline: атрибуция publisher ≠ GovData, дедуп, качество AI.

### Starter packages (проверены CSV + DL-DE BY 2.0)

- `durchschnittsalter-der-bevolkerung-in-deutschland-ab-1871`
- `bevolkerung-in-deutschland-nach-altersgruppen-ab-1871`
- `preisentwicklung-der-jahre-1991-bis-2018`

### Production-конфигурация

```env
GOVDATA_CKAN_BASE_URL=https://ckan.govdata.de/api/3/action
GOVDATA_PACKAGE_IDS=durchschnittsalter-der-bevolkerung-in-deutschland-ab-1871,bevolkerung-in-deutschland-nach-altersgruppen-ab-1871,preisentwicklung-der-jahre-1991-bis-2018
GOVDATA_MAX_RESPONSE_BYTES=500000
GOVDATA_REQUEST_DELAY_SECONDS=0.5
GOVDATA_MAX_PACKAGES_PER_RUN=20
```

### Критерии готовности

- [x] Ни один resource с blocked/NC/ND лицензией не создаётся; unknown не auto-publish.
- [x] Лицензия/контент перепроверяются через content-hash revision при изменении.
- [x] Медиа и сторонние материалы (pdf/zip/images/…) исключаются.

---

## 4. data.europa.eu

Статус: MVP реализован (Search API allowlist). Портал — только discovery;
лицензия и данные берутся у distribution / original publisher.

### Что нужно реализовать

- [x] Подключить Search API (`/search`, `/datasets/{id}`) как discovery-слой.
- [x] Проверять `licence` / `rights` каждой distribution.
- [x] Использовать тот же `open_license_gate`, что и для GovData.
- [x] Блокировать NC, ND, ShareAlike; unknown → `rights_verified=False` → NEEDS_REVIEW.
- [x] ShareAlike явно в blocked markers (не auto-publish).
- [x] Загружать данные у оригинального publisher (`access_url` / `download_url`).
- [x] Ручная проверка неоднозначных rights через модерацию LICENCE.
- [x] Задеплоить и выставить `DATA_EUROPA_DATASET_IDS` на prod
      (`DATA_EUROPA_MAX_DISTRIBUTIONS_PER_DATASET=1`).
- [ ] Подтвердить pipeline: publisher ≠ data.europa.eu, дедуп, качество AI.

### Starter datasets

- `https-www-regionalstatistik-de-genesisws-downloader-00-tables-aig-08-2_00`
- `https-www-regionalstatistik-de-genesisws-downloader-00-tables-ai-n-07_00`
- `05211a5d-6d0e-463b-8cc5-4c5bb51a3623` (Darmstadt ALO; лимит distributions/run)

### Production-конфигурация

```env
DATA_EUROPA_SEARCH_BASE_URL=https://data.europa.eu/api/hub/search
DATA_EUROPA_DATASET_IDS=https-www-regionalstatistik-de-genesisws-downloader-00-tables-aig-08-2_00,https-www-regionalstatistik-de-genesisws-downloader-00-tables-ai-n-07_00,05211a5d-6d0e-463b-8cc5-4c5bb51a3623
DATA_EUROPA_MAX_RESPONSE_BYTES=500000
DATA_EUROPA_REQUEST_DELAY_SECONDS=0.5
DATA_EUROPA_MAX_DISTRIBUTIONS_PER_DATASET=3
```

### Критерии готовности

- [x] Наличие dataset на портале само по себе не даёт `rights_verified`.
- [x] В raw/processed указан оригинальный publisher, не data.europa.eu.
- [ ] Attribution и ссылка на лицензию проверены в UI/Telegram/Share на staging.

---

## 5. Wikinews DE

Статус: только архив. Немецкий Wikinews закрыт 04.05.2026 и не подходит как
источник актуальных новостей.

- [ ] Не включать в основной scheduler.
- [ ] При необходимости создать отдельный архивный режим.
- [ ] Указывать `de.wikinews.org` и CC BY 2.5 для каждого текста.
- [ ] Проверять лицензию каждого изображения отдельно.

---

## Рекомендуемый порядок

1. [x] Активировать GENESIS (curated tables).
2. [x] Eurostat с фильтрами `geo=DE` + allowlist datasets.
3. [x] GovData MVP с resource-level license-gate (включить starter packages на prod).
4. [x] data.europa.eu MVP с тем же license-gate (включить starter datasets на prod).
5. Wikinews оставить только для возможного архивного раздела.

## Не относятся к открытым источникам

Без письменного договора или разрешения не подключать:

- DW/GNS;
- dpa;
- Reuters;
- Associated Press.
