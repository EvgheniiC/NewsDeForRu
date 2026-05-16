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

## Диплинки и Telegram

- Кнопка «Читать в приложении» в Telegram использует `{PUBLIC_APP_BASE_URL}/news/{id}` (см. backend).
- В **AndroidManifest** объявлены App Links для `https://simplenewsapp.de/news…` и `https://www.simplenewsapp.de/news…`.
- На сервере (там же, где отдаётся SPA) должны быть доступны:
  - `/.well-known/assetlinks.json` — подставьте **SHA-256 отпечаток** ключа подписи приложения (релиз или отладка). Шаблон лежит в `frontend/public/.well-known/assetlinks.json` и попадает в `dist` при сборке.
  - `/.well-known/apple-app-site-association` — для iOS; замените `APPLE_TEAM_ID` на свой Team ID. Без расширения `.json`; желательно отдавать как `application/json`.

**Отпечаток для Android (пример):**

```bash
# debug keystore (для проверки App Links в разработке)
keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
```

В продакшене используйте отпечаток **upload key** из Google Play Console / вашего keystore.

## iOS (кратко)

1. На Mac: `npx cap add ios`, затем в Xcode — **Signing & Capabilities** → **Associated Domains** → `applinks:simplenewsapp.de` и `applinks:www.simplenewsapp.de`.
2. Убедитесь, что файл `apple-app-site-association` отдаётся по HTTPS с корректным типом.

## Публикация в магазинах

Чеклист и контекст — в корневом `plan_news_app_22_TODO.md`, пункт 8.
