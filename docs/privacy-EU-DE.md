# Datenschutz / Политика конфиденциальности (DE / RU)

**Hinweis:** Technische Vorlage für privaten Betreiber (natürliche Person), Server in Deutschland, Produktion `https://simplenewsapp.de`. Rechtliche Prüfung empfohlen.

**Примечание:** не юридическая консультация. Заполните `VITE_LEGAL_*` в `frontend/.env` (имя и адрес в Германии).

---

## 1. Verantwortliche Stelle / Контролёр

| Feld | Wert (aus `frontend/.env`) |
|------|----------------------------|
| Name | `VITE_LEGAL_OPERATOR_NAME` |
| Anschrift | `VITE_LEGAL_OPERATOR_STREET`, `VITE_LEGAL_OPERATOR_POSTAL_CITY` |
| E-Mail Datenschutz | `VITE_LEGAL_CONTACT_EMAIL` |
| Website | `VITE_PUBLIC_APP_BASE_URL` (Standard: https://simplenewsapp.de) |

Impressum: `/impressum` · Live-Text: `/privacy`

---

## 2. Verarbeitungen (Stand Backend `.env` / Code)

| Daten | Zweck | Rechtsgrundlage |
|-------|-------|-----------------|
| Server-Logs (Zeit, Pfad, Status; keine Secrets) | Betrieb, Fehlerdiagnose | Art. 6 Abs. 1 lit. f |
| SQLite/DB auf Server **DE** (RSS, Artikel, Embeddings, Moderation) | News-Pipeline | Art. 6 Abs. 1 lit. f |
| **OpenAI** (`LLM_PROVIDER=openai`, gpt-4o-mini, api.openai.com) | Zusammenfassung, Übersetzung, Relevanz | Art. 6 Abs. 1 lit. f; USA — SCC Anbieter |
| **Telegram** (`TELEGRAM_NOTIFICATIONS_ENABLED`) | Kanal-Benachrichtigungen | Art. 6 Abs. 1 lit. f |
| **GMX SMTP** (mail.gmx.net) | Passwort-Reset-E-Mail | Art. 6 Abs. 1 lit. b |
| Konto: E-Mail, Passwort-Hash, Refresh-Token | Login, Registrierung | Art. 6 Abs. 1 lit. b |
| Engagement: `anonymous_user_id`, `session_id`, Events | Nutzungsstatistik | **Art. 6 Abs. 1 lit. a** (Banner) |
| JWT `newsfr.auth.*` in localStorage | Sitzung | Art. 6 Abs. 1 lit. b / f |
| `nga_useful_*` lokal | UI-Markierung | lokal; Server-Sync nur mit Einwilligung |
| Sentry / Prometheus | — | derzeit deaktiviert (leer / false) |
| og:image-Fetch | — | derzeit `OG_IMAGE_FETCH_ENABLED=false` |

---

## 3. Speicherdauer

- Server-Logs: bis **90 Tage** (Hoster-abhängig).
- `user_engagement_events`: **12 Monate**.
- Kontodaten: bis Löschung; Refresh-Token max. **14 Tage**.
- Passwort-Reset-Token: **60 Minuten** (`PASSWORD_RESET_EXPIRE_MINUTES`).
- Artikel-DB: Dauer des Betriebs.

---

## 4. Auftragsverarbeiter / Subprozessoren

1. **Hosting VPS/Server — Deutschland** (Application + Datenbank).
2. **OpenAI, L.L.C.** (USA) — Textverarbeitung.
3. **Telegram** — Bot-API für Veröffentlichungskanal.
4. **GMX (1&1 Mail)** — transaktionale E-Mails.

Keine aktive Nutzung: Sentry, öffentliches Prometheus.

---

## 5. Browser (TTDSG)

| Schlüssel | Ohne Einwilligung | Mit Einwilligung (Banner) |
|-----------|-------------------|---------------------------|
| `newsfr.auth.access_token` / `refresh_token` | ja (eingeloggt) | — |
| `nga_useful_<newsId>` | ja (nur lokal) | — |
| `nga_analytics_consent` | gesetzt bei Wahl | — |
| `nga_anonymous_user_id` | nein | ja |
| `nga_session_id` (sessionStorage) | nein | ja |
| POST `/engagement/events` | nein | ja |

Implementierung: `frontend/src/lib/analyticsConsent.ts`, `AnalyticsConsentBanner`.

---

## 6. Betroffenenrechte (Art. 15–21)

Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch (lit. f), Widerruf Einwilligung (Analytik), Beschwerde bei Landesdatenschutzbehörde.

---

## 7. Impressum (§ 5 TMG)

Separat unter `/impressum` — gleiche Kontaktdaten wie oben.

---

## 8. Checkliste vor Go-Live

- [ ] `VITE_LEGAL_*` in Production-Build gesetzt
- [ ] Impressum zeigt vollständige Anschrift
- [ ] Consent-Banner getestet (Akzeptieren / Ablehnen / Widerruf auf `/privacy`)
- [ ] AV-Verträge mit Hoster, OpenAI, GMX (soweit erforderlich)
- [ ] Keine Secrets in Git (`.env` nur lokal)
