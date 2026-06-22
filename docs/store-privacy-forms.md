# Google Play Data safety и Apple App Privacy

**Не юридическая консультация.** Ответы ниже соответствуют коду репозитория на июнь 2026. Перед отправкой сверьте с фактическим прод-окружением (`backend/.env`, `frontend/.env`).

Связанные документы: [`privacy-EU-DE.md`](privacy-EU-DE.md), [`frontend/MOBILE.md`](../frontend/MOBILE.md).

---

## 1. URL для листинга в сторах

| Поле | Значение |
|------|----------|
| Privacy policy URL | `https://simplenewsapp.de/privacy` (или ваш `VITE_PUBLIC_APP_BASE_URL` + `/privacy`) |
| Impressum (для сайта, не обязателен в сторе) | `https://simplenewsapp.de/impressum` |
| Поддержка / контакт | `VITE_LEGAL_CONTACT_EMAIL` из `frontend/.env` |

В мобильном приложении (Capacitor WebView) те же страницы доступны по маршрутам `/privacy` и `/impressum` — ссылки в шапке [`frontend/src/App.tsx`](../frontend/src/App.tsx).

---

## 2. Инвентаризация данных (по коду)

### 2.1 Без регистрации (все пользователи)

| Данные | Где | На сервер? | Примечание |
|--------|-----|------------|------------|
| HTTP-запросы к API (`GET /news`, …) | Клиент → VPS DE | Да (access-логи) | IP, путь, статус; без секретов |
| `nga_useful_<newsId>` | localStorage | **Нет** | Только UI «полезно»; на сервер уходит **только** при согласии на аналитику (событие `useful`) |
| Решение баннера `nga_analytics_consent` | localStorage | **Нет** | Сервер не знает, кто согласился |

### 2.2 Опциональный аккаунт (`POST /auth/register`, `/login`, …)

| Данные | Эндпоинт | Хранение | Срок |
|--------|----------|----------|------|
| Email | `/auth/register`, `/login` | `app_users.email` | До удаления аккаунта |
| Пароль | регистрация / сброс | bcrypt-хеш в `app_users.password_hash` | — |
| Refresh token | `/auth/refresh` | хеш в `app_refresh_tokens` | до 14 дней |
| Access JWT | ответ API | `localStorage` `newsfr.auth.*` | короткий TTL |

Сброс пароля: `POST /auth/forgot-password` → письмо через **GMX SMTP** (`mail.gmx.net`).

### 2.3 Аналитика (только после «Принять» в баннере)

Реализация: [`frontend/src/lib/analyticsConsent.ts`](../frontend/src/lib/analyticsConsent.ts), [`frontend/src/analytics/engagementQueue.ts`](../frontend/src/analytics/engagementQueue.ts), `POST /engagement/events`.

| Данные | Хранение клиента | Сервер |
|--------|------------------|--------|
| `anonymous_user_id` (UUID) | localStorage `nga_anonymous_user_id` | `user_engagement_events.anonymous_user_id` |
| `session_id` (UUID) | sessionStorage `nga_session_id` | в `payload_json` событий |
| События взаимодействия | очередь → batch POST | `user_engagement_events` |

Типы событий (см. [`backend/app/models/engagement.py`](../backend/app/models/engagement.py)):

- `useful`, `open_preview`, `open_source`, `read_complete_preview`, `read_complete_article`, `expand_full_article`, `navigate_next`, `share`

Payload (примеры): `feed_mode`, `max_ratio`, `dwell_ms`, `channel`, `cached` — **без имени, email, геолокации**.

Срок хранения на сервере: **12 месяцев** (см. [`docs/privacy-EU-DE.md`](privacy-EU-DE.md)).

При «Отклонить» или отзыве согласия: **нет** запросов на `/engagement/events`, **нет** постоянного `anonymous_user_id`.

### 2.4 Что приложение **не** собирает с устройства

- имя, адрес, телефон;
- геолокация, контакты, фото, файлы, календарь;
- рекламный ID (GAID / IDFA) — **нет SDK** Firebase, Google Analytics, Facebook и т.п.;
- crash/analytics SDK — Sentry в бэкенде **выключен** по умолчанию.

Мобильные зависимости: только `@capacitor/core`, `@capacitor/app`, `@capacitor/android` — **без** сторонней аналитики.

### 2.5 Серверная обработка (не с устройства пользователя)

| Сервис | Данные | Связь с мобильным клиентом |
|--------|--------|----------------------------|
| **OpenAI** | RSS-тексты, полные статьи для перевода | Пользователь может вызвать `GET /news/{id}/full-article`; на OpenAI уходит **контент статьи**, не email пользователя |
| **Telegram** | уведомления о новых новостях | Пользовательские PII **не** отправляются |
| **GMX SMTP** | email при сбросе пароля | Только если пользователь запросил reset |

Для форм сторов: указывайте передачу **email** процессору почты (GMX). Передачу **текста статей** в OpenAI можно описать как обработку контента сервисом (часто не попадает в «данные пользователя» в Data safety, если не отправляете профиль/идентификаторы на OpenAI — в вашем коде не отправляете).

---

## 3. Google Play Console — Data safety

Путь: **App content → Data safety → Start / Manage**.

### 3.1 Общие вопросы

| Вопрос | Ответ |
|--------|--------|
| Does your app collect or share any of the required user data types? | **Yes** |
| Is all of the user data collected by your app encrypted in transit? | **Yes** (prod API HTTPS; `https://simplenewsapp.de`) |
| Do you provide a way for users to request that their data is deleted? | **Yes** — email на `VITE_LEGAL_CONTACT_EMAIL` (права GDPR в `/privacy`); удаление аккаунта — по запросу (ручной процесс, опишите в поддержке) |
| Is your app approved for families / directed to children? | **No** (в политике: не для лиц младше 16 лет) |

### 3.2 Типы данных — что отметить

Отмечайте **Collected**. **Shared** — только где данные уходят **третьей стороне** (не ваш VPS). Ниже — рекомендуемая разметка.

#### Personal info → Email address

| Поле | Значение |
|------|----------|
| Collected | Yes |
| Shared | **Yes** (с GMX/1&1 только для транзакционного письма сброса пароля) |
| Ephemeral | No |
| Required or optional | **Optional** (лента без регистрации) |
| Why collected | **App functionality**, **Account management** |
| Why shared | **App functionality** (доставка письма сброса) |

#### Personal info → User IDs

| Поле | Значение |
|------|----------|
| Collected | Yes |
| Shared | **No** (UUID и внутренний user id остаются на вашем сервере) |
| Required or optional | **Optional** (только при согласии на аналитику; JWT — при входе) |
| Why collected | **Analytics** (pseudonymous UUID), **App functionality** (сессия аккаунта) |

*Примечание:* один тип «User IDs» покрывает и `anonymous_user_id`, и идентификатор аккаунта. В комментарии к форме можно указать: «Account session uses internal user id; optional analytics uses random UUID after explicit consent.»

#### App activity → App interactions

| Поле | Значение |
|------|----------|
| Collected | Yes |
| Shared | No |
| Required or optional | **Optional** (только после opt-in баннера) |
| Why collected | **Analytics** |

Примеры: открытие превью, «полезно», шаринг, дочитывание, навигация в ленте.

#### Остальные категории

**Location, Financial, Health, Messages, Photos, Audio, Files, Calendar, Contacts, Web browsing, App info and performance (crash/diagnostics), Device or other IDs (advertising ID)** — **не отмечать**, если в проде не включали Sentry/Prometheus и не добавляли SDK.

### 3.3 Security practices

- **Data is encrypted in transit** — Yes  
- **Committed to Play Families Policy** — No (если не детское приложение)

### 3.4 Текст для поля «Privacy policy»

```
https://simplenewsapp.de/privacy
```

---

## 4. Apple App Store Connect — App Privacy

Путь: **App Privacy → Get Started** (или Edit в разделе приложения).

### 4.1 Сбор данных

**Do you or your third-party partners collect data from this app?** → **Yes**

*(Собственный бэкенд считается сбором; «third-party partners» без рекламных SDK — минимум.)*

### 4.2 Категории и детали

#### Contact Info → Email Address

| Поле | Значение |
|------|----------|
| Linked to user | **Yes** (при регистрации) |
| Used for tracking | **No** |
| Purposes | **App Functionality**, **Account Management** |

#### Identifiers → User ID

| Поле | Значение |
|------|----------|
| Linked to user | **Yes** для аккаунта; для analytics UUID — **Yes** (псевдоним, но привязан к поведению) |
| Used for tracking | **No** (нет кросс-app tracking, нет рекламных сетей) |
| Purposes | **App Functionality** (JWT/сессия), **Analytics** (UUID после согласия) |

#### Usage Data → Product Interaction

| Поле | Значение |
|------|----------|
| Linked to user | **Yes** (связано с anonymous_user_id при согласии) |
| Used for tracking | **No** |
| Purposes | **Analytics** |
| Примечание | Сбор **только** после явного согласия в баннере |

#### Data Not Collected

Не заполняйте лишние категории: Location, Contacts, Browsing History, Purchases, Sensitive Info, Health, Financial Info, Photos/Videos, Audio, Gameplay Content, Customer Support (если не встроен чат), Search History, Surroundings, Body (и т.д.) — **не указывать**.

### 4.3 Privacy Nutrition Label — практическая подсказка

На карточке App Store пользователь увидит примерно:

- **Contact Info** — Email (Linked to You, App Functionality)  
- **Identifiers** — User ID  
- **Usage Data** — Product Interaction  

Это согласуется с опциональной регистрацией и opt-in аналитикой.

### 4.4 Privacy Policy URL

```
https://simplenewsapp.de/privacy
```

(App Store Connect → App Information → Privacy Policy URL)

---

## 5. Согласованность форм, сайта и кода

Перед публикацией проверьте:

- [ ] `VITE_LEGAL_*` заполнены в **production** `npm run build:mobile`
- [ ] `/privacy` и `/impressum` открываются в приложении и в браузере
- [ ] Баннер: «Отклонить» → в Network нет `POST …/engagement/events`
- [ ] «Принять» → появляются запросы `/engagement/events` с `anonymous_user_id`
- [ ] Отзыв согласия на `/privacy` останавливает аналитику
- [ ] Ответы Data safety / App Privacy **не противоречат** тексту `/privacy`
- [ ] В Google Play указан тот же URL политики, что в Apple
- [ ] Если включите Sentry/Prometheus в проде — **обновите** обе формы и `/privacy`

---

## 6. Частые ошибки

| Ошибка | Риск | Как у вас |
|--------|------|-----------|
| Нет URL политики | Отклонение листинга | Указать `…/privacy` |
| Заявили «данные не собираются», но есть регистрация | Блокировка обновлений | Email + User ID — **да** |
| Заявили аналитику без opt-in | Жалоба GDPR / отклонение | Аналитика только после баннера — указать **Optional** |
| Не указали шифрование in transit | Замечание Google | HTTPS на prod API |
| Impressum пустой на сайте | Abmahnung (DE), не стор | Заполнить `VITE_LEGAL_*` |

---

## 7. Краткая шпаргалка (одна таблица)

| Тип данных | Собирается | Обязательно | Shared 3rd party | Цель |
|------------|------------|-------------|------------------|------|
| Email | Да | Нет | GMX (reset mail) | Аккаунт |
| User ID (account + UUID) | Да | Нет | Нет | Сессия / аналитика |
| App interactions | Да | Нет (нужен opt-in) | Нет | Аналитика |
| Пароль | Да (как хеш) | Нет | Нет | Аккаунт |
| Геолокация, рекламный ID, контакты | Нет | — | — | — |

---

*При изменении API (`/auth/*`, `/engagement/events`) или добавлении SDK — обновите этот файл и формы в консолях.*
