# TODO: запросы разрешения у источников (агентства + немецкие СМИ)

Состояние на 10.08.2026.

> Это черновики писем и контакты для outreach. Не юридическая консультация.
> Перед отправкой подставьте реальные данные проекта (название, URL, юрлицо,
> контакт, страна регистрации). Пока нет письменного согласия — материалы
> этих источников в pipeline не подключать (см. `TODO_LIST_OPEN_QUELE.md`).
>
> В коде уже есть RSS-ключи `tagesschau`, `spiegel`, `die_zeit`, `zdf`, `welt`,
> но они с `rights_verified=False` и **намеренно не включаются** через
> `RSS_ENABLED_SOURCE_KEYS`. RSS ≠ право на AI-сводку и публикацию.

## Цель запроса

Попросить **письменное разрешение / доступ к лицензионному продукту** на
использование новостных материалов в приложении для русскоязычных жителей
Германии:

- русскоязычная AI-суммаризация (не дословная перепечатка оригинала);
- человеческая модерация перед публикацией;
- обязательная атрибуция и ссылка на оригинал;
- без фото/видео издания, если отдельно не согласовано;
- без передачи прав третьим лицам.

Такой объём проще согласовать, чем «берём весь RSS и публикуем как есть».

---

## Приоритет outreach

### A. Бесплатный / партнёрский старт

1. [ ] **DW German News Service (GNS)** — самый реалистичный бесплатный канал
      (есть русский трек; явно спросить про AI-summary).
2. [ ] **BAMF** / **BA (Bundesagentur für Arbeit)** / **Bundesregierung (BPA)** —
      бесплатные гос-пресс-источники; нужны письменные условия (не open data
      как Destatis). См. §6 ниже.
3. [ ] **dpa Vertrieb** — если GNS недоступен из‑за гео-ограничений.
4. [ ] **Tagesschau RSS** — уточнить письменно: их публичные условия только
      для **некоммерческих** сайтов; коммерческая app почти наверняка вне правил.

### B. Русскоязычные СМИ о Германии (партнёрство, не «просто RSS»)

5. [ ] **Партнёр (partner-inform.de)** — Dortmund; жизнь/законы DE.
6. [ ] **RusVerlag.de** — новости Германии на русском (Frankfurt).
7. [ ] **Berliner Telegraph** — RU-новости DE. См. §7 ниже.

### C. Немецкие СМИ из исходного списка (много контента, обычно платно)

8. [ ] **DIE ZEIT** — `online-syndication@zeit.de` / форма лицензий.
9. [ ] **WELT** — `nachdrucke@welt.de` + Axel Springer Syndication.
10. [ ] **SPIEGEL** — `syndication@spiegel.de` / форма группы.
11. [ ] **ZDF heute** — `info@zdf.de` / ZDF Studios (коммерческие права).

### D. Международные агентства (обычно платно)

12. [ ] **Reuters** — через sales/licensing form.
13. [ ] **Associated Press** — через sales form.

Реалистично: WELT / ZEIT / SPIEGEL / ZDF дадут **объём**, но почти всегда через
**платную syndication**. Имеет смысл писать после GNS/гос-пресса/RU-партнёров
или параллельно, если есть бюджет на контент.

### Не путать с outreach: Eurostat / GovData / data.europa

Это **не** тема писем о лицензии СМИ. На prod (подтверждено 10.08.2026)
env уже выставлен — ingestion **включён**:

- [x] `EUROSTAT_DATASET_CODES=prc_hicp_midx,une_rt_m,demo_pjan`
- [x] `GOVDATA_PACKAGE_IDS=…` (3 starter packages)
- [x] `DATA_EUROPA_DATASET_IDS=…` (3 starter datasets)
- [x] `GENESIS_DATASET_CODES=…` + token
- [x] RSS: `destatis,ec_press_corner`

Остаётся только качество/атрибуция в UI (см. `TODO_LIST_OPEN_QUELE.md`),
а не «дожать конфиг».

---

## 1. DW / German News Service (GNS)

### Куда писать / куда идти

| Канал | Контакт | Зачем |
| --- | --- | --- |
| GNS (основной) | **gns@dw.com** | доступ к GNS, партнёрство, встраивание DW-контента |
| Регистрация GNS | https://german-news-service.com/about | форма доступа к dpa-материалам в рамках GNS |
| О GNS | https://www.dw.com/en/about-gns/a-65945240 | условия сервиса |
| Общая лицензия DW | форма на https://corporate.dw.com/en/licensing-dw-content/a-77070261 | если нужен не GNS, а отдельный licensing DW |
| TV/film (не наш кейс) | TV.licensing@dw.com | только ТВ-продукции |

Важно: на странице About GNS указано, что часть предложения
**недоступна для German-speaking European countries**. Перед расчётом на
бесплатный dpa-портал GNS нужно явно спросить у `gns@dw.com`, подходит ли
наш кейс (RU-приложение для жителей Германии, оператор в DE/EU).

### Чеклист

- [ ] Заполнить регистрацию на german-news-service.com/about (если доступна).
- [ ] Отправить письмо на `gns@dw.com` (черновик ниже).
- [ ] При необходимости дублировать через DW Licensing request form.
- [ ] Сохранить ответ (PDF/письмо) в `docs/legal/` или внутреннем vault.
- [ ] Только после письменного OK — проектировать ingestion и атрибуцию.

### Черновик письма (EN) — `gns@dw.com`

```text
Subject: Access request – Russian-language news app for residents in Germany

Dear German News Service team,

We operate a news application for Russian-speaking residents in Germany
(project name: [PROJECT_NAME], URL: [URL]).

We would like to request access to / clarification on German News Service
content for editorial use under our brand, with the following intended use:

1) We would prefer an authorized GNS / DW integration path (feed, embed, or
   partner access) rather than scraping public DW pages.
2) For texts we may create a short Russian-language AI-assisted summary for
   our readers; a human moderator reviews items before publication.
3) We always show source attribution and a link to the original item.
4) We do not plan to reuse DW photos/videos/logos unless separately licensed.
5) We do not sublicense or redistribute the original wire feed to third parties.

Could you please confirm:
- whether our project is eligible for GNS (noting the restriction for
  German-speaking European countries);
- which product/access path you recommend;
- the required attribution wording and any AI/summarization restrictions;
- whether a written permission / terms acceptance is available.

Operator / contact:
Name: [FULL_NAME]
Organization / legal entity: [LEGAL_ENTITY]
Country: [COUNTRY]
Email: [EMAIL]
Phone: [PHONE]

Thank you very much for your guidance.
Kind regards,
[FULL_NAME]
```

### Альтернативный короткий вариант (DE) — если пишете по-немецки

```text
Subject: Anfrage Zugang German News Service – App für Russischsprachige in DE

Sehr geehrte Damen und Herren,

wir betreiben eine Nachrichten-App für russischsprachige Einwohnerinnen und
Einwohner in Deutschland ([PROJECT_NAME], [URL]).

Wir bitten um Informationen zum German News Service / zur lizenzierten Nutzung:

- bevorzugter Zugang über GNS/Partner-Feed oder Embed (kein Scraping);
- ggf. kurze russische KI-gestützte Zusammenfassung + menschliche Moderation;
- klare Quellenangabe und Link zum Original;
- zunächst ohne Bilder/Videos/Logos, sofern nicht gesondert lizenziert;
- keine Weitergabe des Feeds an Dritte.

Bitte teilen Sie uns mit, ob unser Vorhaben für GNS infrage kommt
(inkl. Hinweis zu German-speaking European countries), welchen Produktweg
Sie empfehlen und welche schriftlichen Bedingungen gelten.

Kontaktdaten: [NAME], [LEGAL_ENTITY], [EMAIL], [PHONE]

Mit freundlichen Grüßen
[NAME]
```

---

## 2. dpa (Deutsche Presse-Agentur)

### Куда писать

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Vertrieb / продукты | **vertrieb@dpa.com** | консультация по лицензии для сайта/app |
| Kundenservice | **ks@dpa.com** / **cm@dpa.com** | если уже клиент |
| Einzellizenz (отдельные тексты) | **einzellizenz@dpa.com** | разовые тексты (+ форма с dpa.com/de/kontakt) |
| International spot sales | **internationalsales@dpa.com** | EN-форма для отдельных текстов |
| Картинки (отдельно) | sales@picture-alliance.com | только если позже нужны фото |

Стартовать лучше с `vertrieb@dpa.com` (подписка/продукт для app), а не с
разрозненных Einzellizenz на каждый материал.

### Чеклист

- [ ] Отправить запрос в `vertrieb@dpa.com`.
- [ ] Уточнить: WebLines / GNS-связь / app-лицензия / AI-summary правила.
- [ ] Не использовать dpa-тексты до договора/оферты.

### Черновик письма (DE) — `vertrieb@dpa.com`

```text
Subject: Lizenzanfrage – russischsprachige Nachrichten-App für Deutschland

Sehr geehrte Damen und Herren,

wir entwickeln die App [PROJECT_NAME] ([URL]) mit Nachrichten und
Orientierungshinweisen für russischsprachige Menschen in Deutschland.

Wir möchten eine lizenzierte Nutzung von dpa-Inhalten anfragen – idealerweise
als Produkt für Website/App, nicht als unerlaubte Übernahme öffentlicher Texte.

Geplante Nutzung:
- Auswahl Deutschland-/Alltagsrelevanter Meldungen;
- kurze russische redaktionelle/KI-gestützte Zusammenfassung;
- menschliche Freigabe vor Veröffentlichung;
- Quellenangabe „dpa“ + Link/Referenz nach Ihren Vorgaben;
- zunächst ohne Bildfunk/Video, sofern nicht gesondert lizenziert;
- keine Unterlizenzierung an Dritte.

Bitte senden Sie uns Informationen zu geeigneten Produkten, Preismodellen
(auch Pilot/Test, falls möglich) und den Bedingungen für KI-Zusammenfassungen.

Kontaktdaten:
[NAME], [LEGAL_ENTITY], [ADDRESS], [EMAIL], [PHONE]

Mit freundlichen Grüßen
[NAME]
```

---

## 3. Reuters

### Куда писать

Публичного единого «permissions@» для полного wire обычно нет — через формы:

| Канал | URL / контакт | Зачем |
| --- | --- | --- |
| License Reuters Content | https://reutersagency.com/license-reuters-content/ | sales по лицензии контента |
| Contact sales | https://reutersagency.com/contact-us/ | общий вход в sales |
| Text reprints (отдельные тексты) | через Thomson Reuters Rights & Permissions (формы на thomsonreuters.com copyright pages) | разовые reprints |

Ожидание: коммерческая лицензия; «бесплатно для app» маловероятно.

### Чеклист

- [ ] Заполнить License Reuters Content form текстом ниже.
- [ ] Сохранить ticket/confirmation email.
- [ ] Не подключать Reuters без подписанных terms.

### Текст для формы (EN)

```text
We operate [PROJECT_NAME] ([URL]), a news app for Russian-speaking residents
in Germany.

We request information on licensing Reuters text for:
- limited selection of Germany-relevant stories;
- short Russian AI-assisted summaries with human moderation;
- clear attribution and link to the original Reuters item;
- no photo/video reuse unless separately licensed;
- no sublicensing of the feed.

Please advise suitable publisher products, pricing for a small digital
service, and any restrictions on AI summarization.

Contact: [NAME], [LEGAL_ENTITY], [EMAIL], [PHONE], Country: [COUNTRY]
```

---

## 4. Associated Press (AP)

### Куда писать

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Sales / enterprise licensing | форма https://www.ap.org/contact-us/contact-sales/ | подписка text/photos/video |
| AP Images | apimages@ap.org | только фото/графика |
| Reprints отдельных статей | ap@wrightsmedia.com (Wright’s Media) | разовые reprints |
| Copyright notices | copyright@ap.org | претензии/infringement, не sales |

Для нашего кейса: сначала **Contact sales** form (enterprise / digital).

### Чеклист

- [ ] Отправить через AP Contact sales (тип: company/enterprise subscriptions).
- [ ] Если нужны только occasional reprints — отдельно Wright’s Media.
- [ ] Не подключать AP без договора.

### Текст для формы (EN)

```text
Organization: [LEGAL_ENTITY]
Product: [PROJECT_NAME] ([URL]) – news app for Russian-speaking residents in Germany.

Request: licensing options for AP text (Germany/Europe-relevant selection) for
digital publication as short Russian summaries with human moderation, full
attribution, and link-out to the source. No AP photos/video initially.
No sublicensing.

Please share eligible products, pricing for a small digital publisher, and
rules regarding AI-assisted summarization.

Contact: [NAME], [EMAIL], [PHONE], Country: [COUNTRY]
```

---

## 5. Исходные немецкие RSS (Tagesschau, ZEIT, WELT, SPIEGEL, ZDF)

В `backend/app/services/rss_sources.py` они уже заведены как кандидаты, но без
`rights_verified`. Контента у них действительно много — это лучший путь к
«живой» ленте, но только после syndication/письменного OK.

### Общий черновик (DE) — подставить имя издания и email

```text
Subject: Lizenzanfrage – Nutzung von [MEDIENMARKE]-Inhalten in RU-News-App

Sehr geehrte Damen und Herren,

wir betreiben die App [PROJECT_NAME] ([URL]) mit Nachrichten für
russischsprachige Einwohnerinnen und Einwohner in Deutschland.

In unserem System ist bereits ein RSS-Zugang zu [MEDIENMARKE] vorgesehen
(technisch vorbereitet), aber wir nutzen die Inhalte bewusst noch nicht –
wir möchten zuerst eine schriftliche Lizenz / Freigabe klären.

Geplante Nutzung:
- Auswahl deutschlandrelevanter Meldungen;
- kurze russische KI-gestützte Zusammenfassung (kein Vollabdruck des Originals);
- menschliche Moderation vor Veröffentlichung;
- Quellenangabe + Link zum Originalartikel;
- zunächst ohne Fotos/Videos/Logos, sofern nicht gesondert lizenziert;
- keine Unterlizenzierung / Weitergabe des Feeds an Dritte.

Bitte teilen Sie uns mit:
1) ob ein Syndication-/Lizenzprodukt für eine digitale App verfügbar ist;
2) Preisrahmen (auch Pilot/Test, falls möglich);
3) ob KI-Zusammenfassungen zulässig sind und welche Attribution Pflicht ist.

Kontaktdaten: [NAME], [LEGAL_ENTITY], [EMAIL], [PHONE]

Mit freundlichen Grüßen
[NAME]
```

### 5.1 Tagesschau (ARD-aktuell) — ключ `tagesschau`

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Условия RSS | https://www.tagesschau.de/rssfeed-ts-104.html | публичные правила |
| Контакт | формы на https://www.tagesschau.de/kontakt | уточнить коммерческое использование |
| Техн. | webmaster@tagesschau.de | не licensing desk; лучше формы |

Критично: публичные условия разрешают RSS **только некоммерческим** сайтам,
без архивации и без передачи третьим лицам. Наша app с AI-сводками почти наверняка
**не вписывается** без отдельного разрешения.

- [ ] Прочитать актуальные RSS-условия на tagesschau.de.
- [ ] Написать через контакт-форму: коммерческая RU-app + AI-summary — допустимо ли.
- [ ] Не включать `tagesschau` в `RSS_ENABLED_SOURCE_KEYS` без письменного OK.

### 5.2 DIE ZEIT — ключ `die_zeit`

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Online-лицензии | **online-syndication@zeit.de** | веб/app использование |
| Общая syndication | **syndication@zeit.de** | Nachdrucke/Lizenzen |
| Форма | https://www.zeit-verlagsgruppe.de/geschaeftskunden/nachdrucke-und-lizenzen/lizenzanfrage/ | структурированный запрос |
| TDM/коммерческий mining | online-syndication@zeit.de (см. impressum zeit.de) | явно резервируют права |

- [ ] Отправить запрос на `online-syndication@zeit.de` (+ форма).
- [ ] Уточнить пакет/цену для регулярной digital-лицензии, не только single reprint.

### 5.3 WELT — ключ `welt`

| Канал | Контакт | Зачем |
| --- | --- | --- |
| WELT Nachdrucke | **nachdrucke@welt.de** | коммерческое использование статей |
| Axel Springer Syndication | **anfrage@axelspringer.de** | content syndication / пакеты |
| Info | https://www.axelspringer-syndication.de/ | продукты группы |

В impressum WELT прямо: коммерческая перепечатка/онлайн только с согласия.

- [ ] Письмо на `nachdrucke@welt.de` и/или `anfrage@axelspringer.de`.
- [ ] Спросить про регулярный digital feed / app-лицензию.

### 5.4 DER SPIEGEL — ключ `spiegel`

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Syndication | **syndication@spiegel.de** | Nachdruckrechte |
| Форма | https://gruppe.spiegel.de/syndication/anfrage | официальный запрос |
| Тел. | +49 40 3007-3540 / -3550 | уточнения |

Для перевода/публикации SPIEGEL **вне немецкоязычного рынка** часть прав
передана NYT Licensing Group — уточнить, нужен ли отдельный трек для RU.

- [ ] Запрос через форму + `syndication@spiegel.de`.
- [ ] Уточнить: RU-summary в DE-app = «Deutschland» или «Ausland»-трек.

### 5.5 ZDF heute — ключ `zdf`

| Канал | Контакт | Зачем |
| --- | --- | --- |
| B2B | **info@zdf.de** | деловые запросы |
| Presse | pressedesk@zdf.de | журналистские, не app-лицензия |
| Коммерческие права | ZDF Studios / zdf-studios.com | лицензирование контента |
| Контакт-хаб | https://www.zdf.de/unternehmen/dein-zdf/kontakt-700.html | маршрутизация |

- [ ] Письмо на `info@zdf.de` с просьбой направить к digital/syndication.
- [ ] При ответе Studios — отдельно согласовать текст vs видео (нам нужен текст).

### Чеклист после согласия любого из СМИ

- [ ] Получить письменные terms (email/PDF/договор).
- [ ] Выставить `rights_verified=True` + licence/copyright_holder в `rss_sources.py`.
- [ ] Включить ключ в `RSS_ENABLED_SOURCE_KEYS` на staging, потом prod.
- [ ] Проверить атрибуцию в UI / Telegram / Share.
- [ ] Не брать фото из RSS, если лицензия только на текст.

---

## 6. Бесплатные гос-источники (нужно письмо / явные условия)

Не open data «как Destatis». RSS у ведомств есть, но **коммерческая RU-app +
AI-суммаризация** почти всегда требует письменного OK. Письма короткие:
спросить допустимость summary + атрибуцию, без фото/лого.

### 6.1 BAMF (миграции / интеграция / языковые курсы)

| Канал | Контакт | Зачем |
| --- | --- | --- |
| RSS overview | https://www.bamf.de/DE/Service/Abonnieren/RSS/rss_node.html | список feeds |
| Meldungen (пример) | `…/RSSNewsfeed_Meldungen.xml` (ссылка со страницы RSS) | тех. endpoint |
| Pressestelle | форма/контакт на https://www.bamf.de/DE/Presse/presse-node.html | разрешение на использование |
| Impressum | https://www.bamf.de/DE/Service/Impressum/impressum-node.html | © на собственные тексты |

- [ ] Прочитать Impressum; не брать картинки без отдельного OK.
- [ ] Письмо в Pressestelle (черновик ниже).
- [ ] Не включать RSS в pipeline до письменного ответа.

### 6.2 Bundesagentur für Arbeit (BA)

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Presse | **zentrale.presse@arbeitsagentur.de** | разрешение на пресс-тексты / app |
| Impressum (портал) | https://www.arbeitsagentur.de/impressum | тексты портала — только с Genehmigung |
| Statistik BA | https://statistik.arbeitsagentur.de/…/Impressum | **данные/таблицы** статистики — свободнее (с источником; не искажать) |

Важно: для **пресс-текстов сайта** BA прямо требует предварительного
разрешения. Отдельно можно опираться на **статистику BA** (таблицы) с
Quellenangabe — ближе к Destatis/Eurostat, но AI-интерпретацию всё равно
помечать как изменение/собственный расчёт.

- [ ] Письмо на `zentrale.presse@arbeitsagentur.de` про пресс-RSS/тексты.
- [ ] Параллельно оценить ingestion статистики BA (без письма, по Impressum Statistik).

### 6.3 Bundesregierung / BPA (пресс-релизы)

| Канал | Контакт | Зачем |
| --- | --- | --- |
| RSS overview | https://www.bundesregierung.de/breg-de/service/newsletter-und-abos/rss-newsfeed | Pressemitteilungen / kompakt |
| GovData XML | https://data.gov.de/suche/daten/bundesregierung--pressemitteilungen | машинный XML пресс-релизов |
| Kontakt BPA | **internetpost@bundesregierung.de** (Impressum) | запрос на digital reuse / AI-summary |
| Impressum | https://www.bundesregierung.de/breg-de/impressum | условия сайта |

- [ ] Письмо в BPA: RU-app, AI-summary, атрибуция, без фото.
- [ ] Не парсить HTML «на пробу»; только после OK + выбранный feed/XML.

### Общий черновик (DE) — BAMF / BA / BPA

```text
Subject: Anfrage Nutzung von Pressetexten – russischsprachige News-App

Sehr geehrte Damen und Herren,

wir betreiben die App [PROJECT_NAME] ([URL]) mit Nachrichten und
Orientierungshinweisen für russischsprachige Einwohnerinnen und Einwohner
in Deutschland.

Wir möchten klären, ob wir Ihre Pressemitteilungen / öffentlichen Meldungen
unter folgenden Bedingungen nutzen dürfen:

- Auswahl deutschland- und alltagsrelevanter Meldungen;
- kurze russische KI-gestützte Zusammenfassung (kein Vollabdruck);
- menschliche Freigabe vor Veröffentlichung;
- klare Quellenangabe + Link zum Original;
- zunächst ohne Fotos/Videos/Logos;
- keine Unterlizenzierung an Dritte.

Bitte teilen Sie uns mit, ob eine schriftliche Freigabe möglich ist und
welche Attribution Sie verlangen.

Kontaktdaten: [NAME], [LEGAL_ENTITY], [EMAIL], [PHONE]

Mit freundlichen Grüßen
[NAME]
```

---

## 7. Русскоязычные СМИ о Германии (партнёрский outreach)

Контент релевантный аудитории, но **стандартный ©**. Не подключать RSS без
письменного согласия. Цель письма — партнёрство / обмен ссылками / разрешение
на короткие сводки со ссылкой на оригинал (часто реалистичнее, чем у SPIEGEL).

### 7.1 Журнал «Партнёр» — partner-inform.de

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Редакция / издательство | через https://partner-inform.de/ / about; ранее публиковались `m.vaysband@partner-inform.de`, `admin@partner-inform.de` | партнёрство |
| About | https://rss.partner-inform.de/about?lang=ru | ©: распространение только с письменного согласия |

- [ ] Актуализировать email в Impressum/about перед отправкой.
- [ ] Письмо (черновик RU ниже).

### 7.2 RusVerlag.de (LTC Media Verlag)

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Редакция | **redaktion@rusverlag.de** | партнёрство / разрешение |
| Издатель | **a.cherkasky@rusverlag.de** | юр. контакт (Impressum) |
| Контакт | https://rusverlag.de/kontakt | подтвердить актуальные данные |

- [ ] Письмо на `redaktion@rusverlag.de` (+ CC издателю при необходимости).

### 7.3 Berliner Telegraph — berliner-telegraph.de

| Канал | Контакт | Зачем |
| --- | --- | --- |
| Редакция | **info@berliner-telegraph.de** | партнёрство |
| GF / ads | berliner.telegraph.official@gmail.com | если ответят через коммерческий канал |
| Impressum | https://berliner-telegraph.de/impressum/ | юр. данные |

- [ ] Письмо на `info@berliner-telegraph.de`.

### Черновик письма (RU) — диаспорные СМИ

```text
Тема: Партнёрство / разрешение на короткие сводки — приложение для русскоязычных в Германии

Здравствуйте!

Мы развиваем приложение [PROJECT_NAME] ([URL]) — новости и практическая
информация для русскоязычных жителей Германии.

Мы не хотим копировать ваши материалы. Просим рассмотреть партнёрский формат:

1) отбор релевантных материалов по вашей ленте / RSS;
2) короткая русская AI-сводка (не дословная перепечатка) + человеческая модерация;
3) обязательная атрибуция и ссылка на ваш оригинал;
4) без ваших фото/видео/логотипов, если отдельно не согласуем;
5) без передачи ваших текстов третьим лицам.

Если такой формат интересен — напишите, пожалуйста, условия (можно пилот на
N материалов в неделю) или откажите, чтобы мы зафиксировали ответ.

Контакты: [ИМЯ], [ЮРЛИЦО], [EMAIL], [ТЕЛЕФОН]

С уважением,
[ИМЯ]
```

---

## Общие правила до и после ответа

- [ ] В письмах **не утверждать**, что использование уже законно; просить разрешение.
- [ ] Честно указать AI-суммаризацию — скрытие этого повышает риск отказа/отзыва.
- [ ] Хранить согласие: дата, контакт, файл письма, номер договора.
- [ ] После OK обновить `TODO_LIST_OPEN_QUELE.md` и technical attribution checklist.
- [ ] Если отказ / нет ответа 14 дней — источник остаётся в блок-листе.

## Реалистичные ожидания

| Источник | Шанс на доступный старт | Комментарий |
| --- | --- | --- |
| DW GNS | выше | бесплатный сервис; RU-трек; возможны geo-ограничения |
| BAMF / BA / BPA | средний | денег нет, но нужно письмо; BA-статистика проще пресс-текстов |
| Партнёр / RusVerlag / Berliner Telegraph | средний | партнёрство реалистичнее, чем у крупных DE-СМИ |
| dpa напрямую | средний | обычно коммерческий продукт |
| Tagesschau | низкий для коммерции | публичный RSS только non-commercial |
| DIE ZEIT | средний при бюджете | есть явный syndication desk |
| WELT | средний при бюджете | Axel Springer syndication |
| SPIEGEL | средний при бюджете | syndication desk; RU может идти отдельно |
| ZDF | средний/низкий | чаще Studios/индивидуальный договор |
| Reuters | низкий без бюджета | sales + контракт |
| AP | низкий без бюджета | sales + контракт |

## Не делать

- Не включать `tagesschau,spiegel,die_zeit,zdf,welt` в env «на пробу».
- Не парсить сайты изданий / агентств / BAMF / BPA «пока ждём ответ».
- Не подключать RU-диаспорные RSS без письменного OK.
- Не публиковать чужие фото «для красоты» без отдельной лицензии.
- Не считать наличие RSS или молчание согласием.
