# Сборка мобильного клиента (Capacitor)

Веб-приложение упаковывается в **Android** (папка `android/`). **iOS** добавляется командой `npx cap add ios` на macOS с Xcode.

## Требования

- Node.js и зависимости: `npm ci` в каталоге `frontend/`
- **Android:** Android Studio, JDK. На Windows путь к SDK часто задаётся в `android/local.properties` (файл локальный, в git не коммитится).

Если `npm install` падает с ошибкой сертификата (`UNABLE_TO_VERIFY_LEAF_SIGNATURE`), нужно исправить цепочку доверия в системе или корпоративный прокси; временный обход — только на свой страх и риск: `npm config set strict-ssl false`.

## Команды

| Команда | Назначение |
|--------|------------|
| `npm run build` | Прод-сборка **только для веба** (базовый путь `/` — как на VPS). |
| `npm run build:mobile` | Сборка с `--base ./` и **`npx cap sync`** — копирует файлы в `android/`. |
| `npm run cap:open:android` | Открыть проект в Android Studio. |

После изменений фронтенда перед сборкой APK снова выполняйте `npm run build:mobile`.

## Полная статья на русском (только в приложении)

На экране `/news/:id` в **native** (Capacitor) под блоком «Что сделать» есть кнопка **«Читать статью целиком»**. По нажатию вызывается `GET /news/{id}/full-article`: при первом запросе бэкенд скачивает страницу источника, переводит через OpenAI и сохраняет в `processed_news.full_article_ru`; повторные открытия берут текст из БД.

Требования на сервере: `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, миграция `alembic upgrade head`. Опции — в `backend/.env.example` (`FULL_ARTICLE_*`, `OPENAI_FULL_ARTICLE_MODEL`).

## Диплинки и Telegram

- Кнопка «Читать в приложении» в Telegram использует `{PUBLIC_APP_BASE_URL}/news/{id}` (см. backend).
- В **AndroidManifest** объявлены App Links для `https://simplenewsapp.de/news…` и `https://www.simplenewsapp.de/news…`.
- На сервере (там же, где отдаётся SPA) должны быть доступны:
  - `/.well-known/assetlinks.json` — подставьте **SHA-256 отпечаток** ключа подписи приложения (релиз или отладка). Шаблон лежит в `frontend/public/.well-known/assetlinks.json` и попадает в `dist` при сборке.
  - `/.well-known/apple-app-site-association` — для iOS; замените `APPLE_TEAM_ID` на свой Team ID. Без расширения `.json`; желательно отдавать как `application/json`.

## Push: срочные новости (Android)

Дополнительный канал к Telegram: пользователь включает **«⚡ Срочные push»** в меню «Ещё» (только native Android). На сервер уходит FCM token; бэкенд подписывает его на topic `urgent-news` и шлёт push при автопубликации срочной новости.

### Firebase (клиент)

1. [Firebase Console](https://console.firebase.google.com) → проект → **Add app** → Android, package `de.simplenewsapp.app`.
2. Скачайте **`google-services.json`** → `frontend/android/app/google-services.json` (файл локальный, в git обычно не коммитится).
3. `npm run build:mobile` — плагин `@capacitor/push-notifications` подтянется в Gradle (нужен `google-services` classpath — уже в `android/build.gradle`).

### Firebase (сервер)

1. Firebase → Project settings → **Service accounts** → **Generate new private key** (JSON).
2. Положите JSON на VPS (вне git), укажите путь в `backend/.env`:
   - `PUSH_NOTIFICATIONS_ENABLED=true`
   - `FCM_SERVICE_ACCOUNT_PATH=/path/to/service-account.json`
   - опционально `FCM_URGENT_TOPIC=urgent-news`
3. `pip install -r requirements.txt` (пакет `firebase-admin`), миграция `alembic upgrade head`.

Push **не заменяет** Telegram: это отдельный opt-in для тех, у кого нет Telegram или кто хочет уведомления в приложении.

**Отпечаток для Android (пример):**

```bash
# debug keystore (для проверки App Links в разработке)
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

В продакшене используйте отпечаток **upload key** из Google Play Console / вашего keystore.

## Android Studio: PKIX / SSL при синхронизации Gradle (часто домашний ПК)

Ошибка вроде `unable to find valid certification path to requested target` при загрузке **Gradle** с `services.gradle.org` означает, что **Java не доверяет** сертификату в HTTPS (не обязательно «корпоративная сеть»).

**Сначала проверьте:**

1. **Дата и время** на Windows — должны быть точными.
2. **Антивирус** (Kaspersky, ESET, Avast и т.д.): отключите на время теста **сканирование HTTPS / SSL** или добавьте исключения для `studio64.exe`, `java.exe` / JDK из Android Studio. Это самая частая причина на домашнем интернете.

**Заглушка «без скачивания Gradle по HTTPS из Java»** (если браузер нормально качает файлы):

1. В браузере скачайте архив той же версии, что в проекте:  
   https://services.gradle.org/distributions/gradle-8.10-bin.zip  
2. Положите файл, например: `C:\Gradle\gradle-8.10-bin.zip` (путь без пробелов проще).
3. Откройте `android/gradle/wrapper/gradle-wrapper.properties` и **замените** строку `distributionUrl` на локальный файл (обратите внимание на экранирование `:` как `\:`):

   ```properties
   distributionUrl=file\:///C:/Gradle/gradle-8.10-bin.zip
   ```

4. Сохраните файл и снова **Sync Project with Gradle Files** в Android Studio.

Дальше Gradle может снова ходить в **Maven** (Google, Central) по HTTPS — если PKIX повторится, без отключения антивирусного SSL-сканирования или импорта сертификата в JDK обычно не обойтись.

## Локальный бэкенд: эмулятор и телефон («Failed to fetch»)

Сборка по умолчанию ходит на `VITE_API_BASE_URL` (часто `http://127.0.0.1:8000`). **Внутри эмулятора** `127.0.0.1` — это сам эмулятор, не ваш ПК.

1. Бэкенд слушайте на всех интерфейсах:  
   `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
2. **Эмулятор:** в `frontend/.env` задайте `VITE_API_BASE_URL=http://10.0.2.2:8000`, затем `npm run build:mobile`.
3. **Физический телефон** (тот же Wi‑Fi): в `frontend/.env` укажите IP ПК, например `http://192.168.1.10:8000` (узнайте в `ipconfig`), снова `npm run build:mobile`. При необходимости разрешите входящие на порт **8000** в брандмауэре Windows для частной сети.
4. CORS: для WebView Capacitor нужен origin **`https://localhost`** — в дефолт `cors_origins` бэкенда это уже добавлено; при своём `CORS_ORIGINS` в `.env` не забывайте его включить.

5. **Смешанный контент:** интерфейс грузится как **https** (`localhost`), локальный API — **http**. В `capacitor.config.ts` включено **`android.allowMixedContent`**, иначе запросы к `http://10.0.2.2:8000` в WebView часто дают **Failed to fetch**.

В манифесте Android включён **`usesCleartextTraffic`** — иначе HTTP к `10.0.2.2` / локальному IP часто блокируется. Прод-API у вас на HTTPS — для релиза в магазине это обычно приемлемо.

## Подключить свой Android-телефон (USB)

1. На телефоне: **Настройки → О телефоне** — 7 раз по «Номер сборки», затем **Для разработчиков** → **Отладка по USB** (вкл).
2. Кабель USB к ПК, режим файлов/MTP, при запросе разрешите **отладку** с этого компьютера.
3. В Android Studio сверху в списке устройств выберите телефон вместо эмулятора и нажмите **Run**.
4. Для API используйте **LAN IP** ПК в `VITE_API_BASE_URL`, как выше (не `10.0.2.2` — это только эмулятор).

## iOS (кратко)

1. На Mac: `npx cap add ios`, затем в Xcode — **Signing & Capabilities** → **Associated Domains** → `applinks:simplenewsapp.de` и `applinks:www.simplenewsapp.de`.
2. Убедитесь, что файл `apple-app-site-association` отдаётся по HTTPS с корректным типом.

## Публикация в магазинах

1. Заполните `VITE_LEGAL_*` и соберите `npm run build:mobile`.
2. Убедитесь, что в приложении открываются `/privacy` и `/impressum`.
3. Заполните формы в консолях по чеклисту: [`docs/store-privacy-forms.md`](../docs/store-privacy-forms.md) (Google Play Data safety, Apple App Privacy, URL политики).
4. Дополнительный контекст — в [`docs/privacy-EU-DE.md`](../docs/privacy-EU-DE.md).
