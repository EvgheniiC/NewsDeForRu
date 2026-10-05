# TODO: новые требования Google Play (память, R8, Zero-Tap Sign-In)

Состояние на 30.08.2026.

> Информационное письмо Play Console от августа 2026. Это **не срочный
> релиз**. Дедлайны: февраль 2027 (память + DEX) и апрель 2027 (перенос
> сессии). Невыполнение → снижение видимости и ограничение публикации.
>
> Официально:
> [Play Console Help — technical quality requirements](https://support.google.com/googleplay/android-developer/answer/17492799)
> [Android Developers Blog — announcement](https://developer.android.com/blog/posts/elevating-app-quality-reducing-memory-usage-and-improving-device-migration)

Приложение: Capacitor WebView (`de.simplenewsapp.app`), опциональный вход
(email/пароль, JWT в `localStorage`). Категория Play: приложение, не игра.

## Цель

К дедлайнам 2027:

1. Не попасть под «bad behavior» по памяти и битмапам.
2. Если DEX > 10 МБ — включить R8 (shrinking / optimization / obfuscation ≥ 25%).
3. Восстанавливать сессию читателя на новом Android без повторного логина
   (Restore Credentials API).

---

## Приоритет

### A. Сейчас (август–октябрь 2026) — только наблюдение

Ничего не публиковать «из‑за письма». Сбор фактов.

1. [ ] После следующей загрузки AAB открыть **Play Console → App bundle explorer**
       и записать размер DEX (compressed / uncompressed).
       - Если **DEX ≤ 10 МБ** — пункт B формально не обязателен, но R8 всё равно
         желателен как практика.
       - Если **DEX > 10 МБ** — пункт B становится обязательным к февралю 2027.
2. [ ] Когда в Console появятся метрики **Android vitals → Memory**, снять P90:
       - Memory usage (Anonymous RSS + Swap) по RAM-тирам и состояниям
         (Foreground / User-perceived services / Background / Cached);
       - Bitmap memory usage (фон > 200 МБ, cached > 400 МБ — порог нарушения).
3. [ ] Сохранить скрин/цифры в этот файл (раздел «Замеры»).

Ориентир по памяти для **приложений** (P90, февраль 2027):

| RAM устройства | Foreground | Background / UPS |
| --- | --- | --- |
| 4 ГБ | 2 ГБ | 1 ГБ |
| 6–8 ГБ | 2.25 ГБ | 1.25–1.5 ГБ |
| 12 ГБ | 3.25 ГБ | 1.75 ГБ |
| 16 ГБ | 4.25 ГБ | 2 ГБ |
| 16 ГБ+ / устройства < 4 ГБ | порог не задан | порог не задан |

Для новостного WebView эти цифры почти наверняка недостижимы без утечки.
Действие — мониторинг, не рефакторинг.

### B. До февраля 2027 — R8 / minify (если DEX > 10 МБ или «на всякий случай»)

Сейчас в `frontend/android/app/build.gradle`:

```
release { minifyEnabled false }
```

`proguard-rules.pro` — шаблон Capacitor, keep-правил нет.

4. [ ] Включить `minifyEnabled true` и `shrinkResources true` для `release`.
5. [ ] Добавить keep-правила для Capacitor / плагинов / JS-bridge
       (WebView JavaScript interface, reflection в плагинах).
       Не включать R8 вслепую: ломает native plugins.
6. [ ] Собрать release AAB, загрузить в internal testing.
7. [ ] В App bundle explorer проверить, что shrinking / optimization /
       obfuscation ≥ **25%** каждое (если DEX > 10 МБ).
8. [ ] Прогнать смоук: старт, App Links, пуши, логин/логаут, модерация,
       шаринг через FileProvider.
9. [ ] Документация R8:
       [Enable app optimization](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization)

### C. До апреля 2027 — Zero-Tap Sign-In (обязательно)

Google: любое приложение **с входом** (обязательным *или* опциональным)
должно восстанавливать сессию при переносе Android → Android
(device-to-device или cloud backup) через
[Restore Credentials API](https://developer.android.com/identity/sign-in/restore-credentials)
(Credential Manager). Доступно с Android 9.

`android:allowBackup="true"` и случайный бэкап `localStorage` **не засчитываются**.
Play проверяет успешный retrieve restore key.

Текущее состояние:

- JWT: `newsfr.auth.access_token` / `newsfr.auth.refresh_token` в `localStorage`
  (`frontend/src/context/AuthContext.tsx`);
- Restore Credentials / Block Store — нет;
- игры, банки, медицина, приложения без логина — исключения; мы не в списке.

10. [ ] Спека: что кладём в restore key (не сам access JWT, а opaque restore
        token / refresh, который бэкенд обменяет на новую пару).
11. [ ] Backend: эндпоинт выдачи restore-токена при логине и обмена на
        access+refresh на новом устройстве; инвалидация при logout / удалении
        аккаунта (Google: при logout restore key надо **явно удалить**).
12. [ ] Capacitor-плагин (или тонкая Kotlin-обвязка):
        - `createRestoreCredential` после успешного логина / refresh сессии;
        - `getRestoreCredential` при холодном старте, если localStorage пуст;
        - `deleteRestoreCredential` при logout и удалении аккаунта.
13. [ ] JS: в `AuthContext` — попытка restore до показа «не залогинен»;
        гостевой пользователь на старом устройстве остаётся гостем на новом
        (требование Google).
14. [ ] Несколько аккаунтов: restore key только для **активного** (последнего)
        пользователя.
15. [ ] Тесты в Android Studio по
        [Test Restore Credentials](https://developer.android.com/identity/sign-in/restore-credentials-test).
16. [ ] Privacy / Impressum: кратко описать перенос сессии на новое устройство
        (DE + RU тексты).
17. [ ] Релиз в production **до апреля 2027** (лучше за 1–2 месяца, чтобы
        Play успел увидеть restore key retrieval).

Не использовать Block Store как «новый» путь: compliant только интеграции
**в production до 30.09.2026**. Мы этот поезд уже не успеваем / не хотим —
идти сразу в Credential Manager.

### D. Память — только если vitals красные

18. [ ] Если P90 памяти/битмапов близко к порогу: `onTrimMemory` в
        `MainActivity`, не копить картинки в фоне, проверить WebView cache.
        Для этого приложения маловероятно.

---

## Порядок работ (когда дойдём руками)

1. Замеры DEX + Memory в Play Console (A).
2. R8, если нужен по размеру DEX (B).
3. Спека restore token на бэкенде (C.10–11).
4. Native plugin + `AuthContext` (C.12–14).
5. Тесты переноса + privacy (C.15–16).
6. Production-релиз с запасом до апреля 2027 (C.17).

Не смешивать с контент-outreach (`TODO_LIST_SEND_EMAIL_TO_QUELLE.md`) и
источниками (`TODO_Quellen.md`). Это отдельный Android/Play трек.

---

## Замеры (заполнять после загрузок AAB)

| Дата | versionName / versionCode | DEX size | Shrink % | Optimize % | Obfuscate % | Memory P90 FG | Bitmap BG | Примечание |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| | 1.2.10 / 28 | | minifyEnabled=false | | | | | исходная точка |

---

## Что не делать

- Не делать срочный патч из‑за письма августа 2026.
- Не включать R8 без keep-правил и internal testing.
- Не считать Auto Backup / `localStorage` выполнением Zero-Tap.
- Не требовать повторный пароль/MFA сразу после device-to-device restore
  (Google: proof of possession уже есть; identity restore достаточно).
- Не менять категорию приложения на «игру», чтобы обойти пороги —
  нарушение metadata policy.
