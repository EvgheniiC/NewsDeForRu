# Juristische TODO-Liste vor dem Deployment

Stand: 02.08.2026

> Arbeits- und Prüfcheckliste, keine Rechtsberatung. Die finale Freigabe sollte durch eine in Deutschland zugelassene Kanzlei mit Schwerpunkt Urheberrecht, Presserecht, Datenschutz und IT-Recht erfolgen.

## Freigaberegel

Kein Produktionsstart und keine Einreichung bei App Store oder Google Play, solange ein Punkt unter **P0 — Deployment-Blocker** offen ist.

## P0 — Deployment-Blocker

### 1. Nutzungsrechte für jede Nachrichtenquelle klären

- [x] Für Tagesschau, Spiegel, Die Zeit, ZDF und WELT die aktuellen RSS-Nutzungsbedingungen dokumentieren.
- [ ] Pro Quelle schriftlich klären, ob kommerzielle Aggregation, Speicherung, Übersetzung, KI-Zusammenfassung, Telegram-Veröffentlichung und Push-Benachrichtigungen erlaubt sind.
- [x] Wenn eine erforderliche Nutzung nicht eindeutig erlaubt ist, eine Lizenz einholen oder die Quelle deaktivieren.
- [ ] Ansprechpartner, Lizenztext, Abrufdatum, zulässige Felder und Widerrufsbedingungen pro Quelle dokumentieren.
- [x] Einen Prozess für regelmäßige Neuprüfung geänderter RSS- und Website-Bedingungen festlegen.
- [ ] Sicherstellen, dass nur Fakten, eigene Zusammenfassungen und einzelne Wörter beziehungsweise sehr kurze Auszüge veröffentlicht werden.
- [ ] Keine RSS-Beschreibung unverändert oder nahezu unverändert als Ersatz für die Originalpublikation anzeigen.
- [ ] Die zulässige Länge und Art von Snippets durch einen deutschen Urheberrechtsanwalt bewerten lassen; keine pauschale Zeichengrenze als rechtssicher annehmen.
- [x] Prüfen, ob automatisierte Abrufe durch maschinenlesbare Nutzungsvorbehalte, robots.txt oder Nutzungsbedingungen ausgeschlossen werden.

Dokumentation:

- Quellen- und Lizenzregister: `docs/source-rights-register.md`
- Vorlage für schriftliche Lizenzanfragen: `docs/source-license-request-de.md`
- Technische Sperre: `RSS_ENABLED_SOURCE_KEYS` ist standardmäßig leer; eine Quelle
  wird nur nach expliziter Aufnahme in diese Allowlist abgerufen.
- Vorläufiges Ergebnis: Keine der fünf Quellen ist für den vollständigen geplanten
  Produktionsumfang eindeutig freigegeben. Bis zur schriftlichen Klärung müssen
  die Quellen technisch deaktiviert bleiben.

Relevante Normen zur anwaltlichen Prüfung:

- §§ 16, 19a, 23, 44b UrhG
- §§ 87f–87k UrhG, insbesondere § 87g UrhG
- Art. 15 Richtlinie (EU) 2019/790

### 2. Unzulässige Originalfragmente im AI-Fallback verhindern

- [x] Automatische Tests ergänzen, die längere Übereinstimmungen zwischen RSS-Original und veröffentlichter Fassung erkennen.
- [x] Vor Veröffentlichung auf ungewöhnlich hohe Textähnlichkeit zum Original prüfen.
- [ ] Bereits veröffentlichte Beiträge auf übernommene Originalfragmente untersuchen und problematische Inhalte entfernen.

Betroffene Stelle:

- `backend/app/schemas/llm_output.py`
- `backend/app/services/publisher_text_guard.py`
- `backend/app/services/published_text_audit.py`
- `backend/app/services/pipeline_service.py`
- Dry-Run: `python -m app.scripts.audit_published_text_overlap`
- Quarantäne nach Prüfung des Dry-Runs:
  `python -m app.scripts.audit_published_text_overlap --apply`
- Die Schwellenwerte sind nur technische Sicherheitsregeln und keine
  rechtssicheren Zeichengrenzen.

### 3. Impressum produktionsreif machen

- [ ] Alle produktiven `VITE_LEGAL_*`-Werte mit echten und vollständigen Betreiberangaben befüllen.
- [ ] Name beziehungsweise Firma und Rechtsform angeben.
- [ ] Ladungsfähige vollständige Anschrift angeben; kein Postfach verwenden.
- [ ] Eine unmittelbar erreichbare E-Mail-Adresse und einen weiteren schnellen Kontaktweg prüfen.
- [ ] Falls vorhanden, Register, Registernummer, Umsatzsteuer-ID und vertretungsberechtigte Person ergänzen.
- [ ] Verantwortliche Person nach § 18 Abs. 2 MStV mit vollständigem Namen und Anschrift angeben.
- [ ] Impressum aus jeder App-Ansicht leicht, unmittelbar und dauerhaft erreichbar machen.
- [ ] Deutsche Fassung als rechtlich maßgebliche Fassung kennzeichnen; russische Übersetzung inhaltlich synchron halten.
- [ ] Verweise auf die aktuell geltenden Vorschriften prüfen, insbesondere § 5 DDG statt veralteter TMG-Verweise.
- [ ] Produktionsbuild testen und sicherstellen, dass keine Platzhalter oder Warnungen angezeigt werden.

### 4. Datenschutzerklärung vervollständigen

- [ ] Veraltete Bezeichnung `TTDSG` durch die aktuell geltende Bezeichnung `TDDDG` ersetzen und Rechtsgrundlagen juristisch prüfen.
- [ ] Firebase Cloud Messaging beziehungsweise den verwendeten Push-Dienst ausdrücklich als Empfänger/Auftragsverarbeiter aufnehmen.
- [ ] Verarbeitung von Push-Token, Geräte-/Plattformdaten, Zweck, Rechtsgrundlage, Speicherdauer und Widerruf beschreiben.
- [ ] Löschung beziehungsweise Deaktivierung eines Push-Abonnements technisch und rechtlich dokumentieren.
- [ ] Alle tatsächlich eingesetzten Empfänger aufführen: Hosting, Datenbank, OpenAI, Telegram, Mailserver für noreply@simplenewsapp.de und support@simplenewsapp.de, Firebase/Google und gegebenenfalls Sentry.
- [ ] Für jede Datenkategorie konkrete oder nachvollziehbare Löschfristen nennen.
- [ ] Aufbewahrung und Löschung von `raw_news_items`, `processed_news`, Clustern, Embeddings, Logs, Engagement-Events, Accounts, Refresh-Tokens und Push-Tokens festlegen.
- [ ] Internationale Datenübermittlungen vollständig dokumentieren: Empfängerland, Transfermechanismus, SCC und gegebenenfalls Transfer Impact Assessment.
- [ ] Mit allen relevanten Auftragsverarbeitern Verträge nach Art. 28 DSGVO abschließen und archivieren.
- [ ] Prüfen, ob OpenAI-Inhalte für Training verwendet werden können, und Training soweit vertraglich/technisch möglich deaktivieren.
- [ ] Datenschutzerklärung und tatsächliche Konfiguration auf vollständige Übereinstimmung prüfen.
- [ ] Deutsche Fassung als maßgebliche Fassung kennzeichnen und russische Übersetzung synchron halten.
- [ ] Kontaktdaten der zuständigen Datenschutzaufsichtsbehörde korrekt angeben.
- [ ] Datenschutzerklärung vor dem ersten produktiven Datenfluss öffentlich erreichbar machen.

### 5. Verzeichnis, Risikoanalyse und Betroffenenrechte

- [ ] Verzeichnis der Verarbeitungstätigkeiten nach Art. 30 DSGVO erstellen.
- [ ] Rechtsgrundlage und Interessenabwägung für alle Verarbeitungen nach Art. 6 Abs. 1 lit. f DSGVO schriftlich dokumentieren.
- [ ] Prüfen, ob eine Datenschutz-Folgenabschätzung nach Art. 35 DSGVO erforderlich ist; Entscheidung dokumentieren.
- [ ] Prozess für Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch und Datenübertragbarkeit definieren.
- [ ] Identitätsprüfung und Antwortfrist für Betroffenenanfragen definieren.
- [ ] Technischen Export und die vollständige Löschung eines Nutzerkontos testen.
- [ ] Datenschutzverletzungsprozess einschließlich 72-Stunden-Bewertung nach Art. 33 DSGVO erstellen.
- [ ] Zuständigkeiten und Kontaktkette für Datenschutzvorfälle festlegen.

### 6. Consent und Tracking prüfen

- [ ] Sicherstellen, dass Engagement-Analytics vor ausdrücklicher Einwilligung keinerlei persistente IDs oder Events erzeugt beziehungsweise überträgt.
- [ ] Ablehnen muss genauso einfach und sichtbar sein wie Akzeptieren.
- [ ] Widerruf muss jederzeit möglich sein und zukünftige Übertragungen sofort stoppen.
- [ ] Consent-Status, Textversion und Zeitpunkt lokal nachvollziehbar verwalten.
- [ ] Prüfen, ob technisch notwendige Speicherung korrekt von optionaler Analyse getrennt ist.
- [ ] End-to-End-Test für Akzeptieren, Ablehnen, Widerruf und Löschen lokaler Daten durchführen.
- [ ] Prüfen, ob Referrer, Trackingparameter oder eindeutige Nutzerkennungen an Nachrichtenseiten übertragen werden; diese vermeiden.

### 7. Store-Datenschutzangaben synchronisieren

- [ ] Apple App Privacy vollständig anhand des Produktionsbuilds ausfüllen.
- [ ] Google Play Data Safety vollständig anhand des Produktionsbuilds ausfüllen.
- [ ] Account-, E-Mail-, Nutzungsanalyse-, Push-Token-, Geräte-, Log- und Diagnosedaten korrekt angeben.
- [ ] Optionale und notwendige Verarbeitung korrekt unterscheiden.
- [ ] Datenweitergabe an OpenAI, Google/Firebase, Telegram, den Mailserver für @simplenewsapp.de, Hosting und gegebenenfalls Sentry korrekt angeben.
- [ ] `docs/store-privacy-forms.md` an den tatsächlichen Einsatz von `@capacitor/push-notifications` anpassen.
- [ ] Öffentliche URL zur Datenschutzerklärung und Support-Kontaktdaten vor Einreichung testen.
- [ ] Sicherstellen, dass Store-Angaben, Datenschutzerklärung und tatsächlicher Netzwerkverkehr übereinstimmen.

### 8. Externe Artikel sicher öffnen

- [ ] Originalartikel ausschließlich über ihre offizielle HTTPS-URL öffnen.
- [ ] Für Android Systembrowser oder Custom Tabs verwenden.
- [ ] Für iOS Systembrowser oder `SFSafariViewController` verwenden.
- [ ] Sicherstellen, dass Domain beziehungsweise URL des Herausgebers sichtbar und nicht irreführend überdeckt wird.
- [ ] Eine Aktion „Im Browser öffnen“ anbieten, falls ein In-App-Browser verwendet wird.
- [ ] Keine Werbung, Cookie-Banner, Paywalls, Header oder andere Elemente der Herausgeberseite blockieren oder verändern.
- [ ] Kein JavaScript, CSS oder sonstigen Code in Herausgeberseiten injizieren.
- [ ] Keine Authentifizierung, Bezahlschranke oder technische Schutzmaßnahme umgehen.
- [ ] Weiterleitungen nur auf `http`/`https` erlauben und gefährliche Schemas blockieren.
- [ ] Gegen Open Redirects, Deep-Link-Manipulation und nicht vertrauenswürdige URLs absichern.
- [ ] Prüfen, ob `target="_blank"` im produktiven Capacitor-Build tatsächlich im vorgesehenen sicheren Browser-Kontext öffnet.

### 9. Haftungstexte juristisch prüfen lassen

- [ ] Disclaimer nicht als vollständigen Haftungsausschluss formulieren.
- [ ] Klarstellen, dass es sich um automatisch erstellte Zusammenfassungen handelt und Fehler möglich sind.
- [ ] Klarstellen, dass Originalartikel und Rechte bei den jeweiligen Herausgebern beziehungsweise Rechteinhabern liegen.
- [ ] Verfahren für Meldungen zu Urheberrechtsverletzungen und rechtswidrigen Inhalten einrichten.
- [ ] Kontaktadresse für Takedown-Anfragen veröffentlichen.
- [ ] Interne Fristen für Prüfung, Sperrung, Löschung und Antwort festlegen.
- [ ] Jede Beschwerde und Reaktion revisionsfähig dokumentieren.
- [ ] Haftungs-, Urheberrechts- und Link-Hinweise durch eine deutsche Kanzlei freigeben lassen.

## P1 — Vor Store-Einreichung abschließen

### 10. Quellenangabe und Weitergabe verbessern

- [ ] Auf jeder Detailansicht Herausgeber, Veröffentlichungsdatum und Link zum Original anzeigen.
- [ ] Domain des Ziels vor dem Öffnen erkennbar machen.
- [ ] Kennzeichnung „automatisch erstellte Zusammenfassung, kein Originaltext“ bei allen AI-generierten Textblöcken anzeigen, nicht nur bei der Kurzfassung.
- [ ] Bei WhatsApp-/Telegram-Sharing zusätzlich zur App-URL auch Quelle beziehungsweise Link zum Original aufnehmen.
- [ ] Push-Nachrichten so formulieren, dass sie nicht den Eindruck einer Originalmeldung des Herausgebers erzeugen.
- [ ] Keine Logos, Marken oder Gestaltung verwenden, die eine Kooperation mit dem Herausgeber suggeriert.
- [ ] Prozesse für entfernte oder nachträglich korrigierte Originalartikel definieren.

Betroffene Stellen:

- `frontend/src/components/NewsAttributionBlock.tsx`
- `frontend/src/components/NewsArticleBody.tsx`
- `frontend/src/utils/shareNews.ts`
- `backend/app/services/push_notifier.py`
- `backend/app/services/telegram_notifier.py`

### 11. AI-Ausgaben und redaktionelle Kontrolle

- [ ] Alle AI-generierten redaktionellen Inhalte konsistent kennzeichnen.
- [ ] Prüfen, welche Transparenzpflichten aus Art. 50 der Verordnung (EU) 2024/1689 für Texte und Bilder konkret anwendbar sind.
- [ ] Keine automatisch generierte Meldung veröffentlichen, wenn Quelle, URL, Datum oder Kernaussagen nicht validiert wurden.
- [ ] Für Politik, Wahlen, Gesundheit, Sicherheit, Strafvorwürfe und personenbezogene Behauptungen zwingende manuelle Prüfung erwägen.
- [ ] Korrektur-, Sperr- und Rückrufprozess für fehlerhafte Zusammenfassungen einrichten.
- [ ] Redaktionsrichtlinie für Tatsachen, Meinungen, Zitate und Unsicherheit erstellen.
- [ ] Veröffentlichungsprotokoll mit Quelle, Modellversion, Promptversion, Prüfstatus und Zeitstempel führen.
- [ ] Prüfen, ob Beiträge im Status `needs_review` über direkte API-IDs öffentlich erreichbar sind, und den Zugriff verhindern.
- [ ] Prompt-Injection und manipulierte RSS-Inhalte als Sicherheits- und Redaktionsrisiko testen.

### 12. AI-Bilder

- [ ] Nur Bildmodelle und Assets mit dokumentierten kommerziellen Nutzungsrechten einsetzen.
- [ ] Lizenzbedingungen und Modellversion jeder Bildquelle archivieren.
- [ ] AI-Bilder deutlich als „KI-generierte Illustration“ kennzeichnen.
- [ ] Keine fotorealistische Darstellung realer Ereignisse verwenden, wenn sie als dokumentarische Aufnahme missverstanden werden kann.
- [ ] Keine realen Personen ohne rechtliche Prüfung erkennbar darstellen.
- [ ] Persönlichkeitsrechte, Marken, Logos, Gebäude- und Designrechte prüfen.
- [ ] Herkunfts- beziehungsweise Generierungsnachweise soweit technisch möglich speichern.
- [ ] Prozess für Beschwerden und Entfernung problematischer Bilder einrichten.

### 13. Datensparsamkeit und Sicherheit

- [ ] Produktionsdatenbank, Backups und Objektspeicher ausschließlich mit dokumentierter Zugriffskontrolle betreiben.
- [ ] TLS für sämtliche externen und internen Produktionsverbindungen erzwingen.
- [ ] `HTTP_VERIFY_SSL=false`, Cleartext-Traffic und Mixed Content in Produktionsbuilds ausschließen.
- [ ] Geheimnisse ausschließlich in Secret-Management speichern; keine echten Schlüssel in Repository, APK oder Frontend-Bundle.
- [ ] Passwörter mit einem aktuellen speicherharten Verfahren hashen.
- [ ] Refresh-Tokens rotieren und widerrufbar machen.
- [ ] Rate Limits für Login, Passwort-Reset, Registrierung, Engagement und Push-Endpoints konfigurieren.
- [ ] Logs auf E-Mail-Adressen, Tokens, Artikeltexte und andere unnötige personenbezogene oder geschützte Inhalte prüfen.
- [ ] Backup-Verschlüsselung, Wiederherstellung und fristgerechte Löschung testen.
- [ ] Rollen und minimale Zugriffsrechte für Produktion dokumentieren.
- [ ] Abhängigkeiten und Container vor Release auf bekannte Schwachstellen prüfen.
- [ ] Unabhängigen Security Review vor dem ersten öffentlichen Release durchführen.

### 14. Konten und Nutzerlöschung

- [ ] In-App-Funktion zum Löschen des Kontos bereitstellen, falls Konten erstellt werden können.
- [ ] Anforderungen von Apple und Google zur Kontolöschung prüfen und erfüllen.
- [ ] Öffentliche Web-URL für Löschanfragen bereitstellen, falls Google Play sie verlangt.
- [ ] Definieren, welche Daten sofort gelöscht, anonymisiert oder aufgrund gesetzlicher Pflichten befristet aufbewahrt werden.
- [ ] Löschung in Hauptdatenbank, Push-Abonnements, Tokens, Analytics-Zuordnungen und Backups berücksichtigen.
- [ ] Nutzer vor Abschluss transparent über Folgen und verbleibende Aufbewahrung informieren.

### 15. Jugendschutz und Zielgruppe

- [ ] Tatsächliche Zielgruppe und Store-Altersfreigaben konsistent festlegen.
- [ ] Aussage „nicht für Personen unter 16 Jahren“ technisch und rechtlich auf Plausibilität prüfen.
- [ ] Keine unnötige Altersabfrage oder Verarbeitung von Geburtsdaten einführen.
- [ ] Verfahren für sensible, gewalttätige oder nicht jugendfreie Nachrichteninhalte festlegen.
- [ ] Google Families Policy und Apple Kids Category nur dann auswählen, wenn alle besonderen Anforderungen erfüllt werden.

### 16. Barrierefreiheit

- [ ] Anwendbarkeit des BFSG und der zugehörigen Verordnung prüfen, einschließlich möglicher Ausnahmen.
- [ ] WCAG 2.2 AA als technisches Ziel verwenden.
- [ ] Screenreader, Tastaturnavigation, Kontrast, Textvergrößerung, Fokusführung und reduzierte Animation testen.
- [ ] Links und AI-Bilder mit sinnvollen zugänglichen Bezeichnungen versehen.
- [ ] Falls erforderlich, Barrierefreiheitserklärung und Kontaktweg veröffentlichen.

### 17. Store-Funktionalität und Review

- [ ] Dokumentieren, welchen eigenständigen Mehrwert die App gegenüber einer Website bietet.
- [ ] Apple Guideline 4.2 „Minimum Functionality“ vor Einreichung prüfen.
- [ ] Google-Play-Regeln zu „Webviews and Affiliate Spam“ und eingeschränkter Funktionalität prüfen.
- [ ] Keine Behauptung verwenden, die App oder einzelne Quellen seien offiziell, lizenziert oder partnerschaftlich verbunden, sofern dies nicht nachweisbar ist.
- [ ] Reviewer Notes mit Testkonto, Beschreibung der AI-Summarization, Quellenöffnung, Consent und Push-Opt-in vorbereiten.
- [ ] Android- und später iOS-Produktionsbuild auf realen Geräten testen.
- [ ] Screenshots und Store-Beschreibung müssen die tatsächliche Funktion zeigen.
- [ ] Veraltete Beschreibung der deaktivierten Volltextfunktion aus `frontend/MOBILE.md` und Store-Material entfernen.

## P2 — Betriebsbereitschaft vor öffentlichem Launch

### 18. Takedown- und Incident-Prozess

- [ ] Zentrale Kontaktadresse für Herausgeber, Rechteinhaber und Behörden einrichten.
- [ ] Dringlichkeitsstufen und Reaktionszeiten definieren.
- [ ] Sofortige Deaktivierung einzelner Quellen und Beiträge technisch ermöglichen.
- [ ] Korrekturen und Löschungen an App, API, Telegram, Push und Caches weitergeben.
- [ ] Beweise sichern, ohne beanstandete Inhalte unnötig weiterzuverarbeiten.
- [ ] Wiederholte Verstöße pro Quelle auswerten und Quelle gegebenenfalls sperren.
- [ ] Verantwortliche Vertretung für Urlaub und Ausfälle bestimmen.

### 19. Regelmäßige Compliance-Prüfung

- [ ] Vierteljährliche Prüfung der Quellenbedingungen und Lizenzen terminieren.
- [ ] Vierteljährliche Prüfung von Datenschutzerklärung, Impressum und Store-Formularen terminieren.
- [ ] Bei jeder neuen SDK-, Tracking-, AI-, Hosting- oder Push-Integration eine Datenschutzprüfung verlangen.
- [ ] Datenflüsse und Netzwerkverkehr jedes Release-Builds automatisiert oder manuell vergleichen.
- [ ] Löschfristen regelmäßig ausführen und protokollieren.
- [ ] Jährliche Überprüfung durch Datenschutz- und Urheberrechtsexperten einplanen.
- [ ] Änderungen an UrhG, DSGVO, TDDDG, DDG, MStV, EU AI Act, BFSG sowie Apple-/Google-Regeln beobachten.

## Erforderliche Nachweise für die finale Freigabe

- [ ] Schriftliche juristische Freigabe oder dokumentierte Risikobewertung.
- [ ] Quellen- und Lizenzregister mit Belegen.
- [ ] Vollständiges Impressum ohne Platzhalter.
- [ ] Finale Datenschutzerklärung DE und inhaltlich synchrone Übersetzung RU.
- [ ] Verzeichnis der Verarbeitungstätigkeiten.
- [ ] Auftragsverarbeitungsverträge und Nachweise internationaler Transfers.
- [ ] Lösch- und Aufbewahrungskonzept.
- [ ] Consent-Testprotokoll.
- [ ] Account-Löschtest.
- [ ] Store-Privacy- und Data-Safety-Abgleich.
- [ ] Security-Review und behobene kritische Findings.
- [ ] Nachweis, dass Volltext-Scraping, Vollübersetzung und Volltext-API in Produktion nicht verfügbar sind.
- [ ] Produktionscheck von Impressum-, Datenschutz-, Quellen- und Takedown-Links.

## Finale Go/No-Go-Abnahme

- [ ] Product Owner bestätigt, dass alle P0-Punkte abgeschlossen sind.
- [ ] Datenschutzverantwortliche Person bestätigt DSGVO/TDDDG-Unterlagen.
- [ ] Technische Leitung bestätigt Produktionskonfiguration und Löschungen.
- [ ] Juristische Beratung bestätigt das verbleibende Urheberrechts- und Presserechtsrisiko.
- [ ] Store-Angaben wurden gegen den final signierten Build geprüft.
- [ ] Entscheidung und Version der geprüften Dokumente wurden schriftlich archiviert.

