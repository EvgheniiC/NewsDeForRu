# TODO: Quellen für das kommerzielle Nachrichtenprojekt

Stand der Recherche: 02.08.2026

> Arbeitsdokument, keine Rechtsberatung. Vor der produktiven Nutzung müssen die
> konkrete Lizenz des Materials, die technische Zugriffsmethode und alle
> abweichenden Hinweise der jeweiligen Seite erneut geprüft werden.

## Kurzantwort zur Firma

Für offene Quellen wie Destatis, Eurostat, European Commission, GovData und
data.europa.eu ist keine Firma, kein Gewerbe und grundsätzlich kein
Lizenzvertrag erforderlich.

Für eine erste Anfrage oder einen Test bei dpa, Reuters, AP oder DW ist eine
GmbH ebenfalls nicht zwingend erforderlich. Beim Abschluss eines
kommerziellen Vertrags wird jedoch ein eindeutig bestimmter Vertragspartner
mit Rechnungs- und Kontaktdaten benötigt. Das kann grundsätzlich auch ein
Einzelunternehmen sein; ob der jeweilige Anbieter einen noch nicht
registrierten Gründer akzeptiert, muss schriftlich geklärt werden.

Vor einem kommerziellen öffentlichen Start müssen unabhängig von der
Quellenlizenz die gewerbe-, steuer- und impressumsrechtlichen Anforderungen
des eigenen Angebots erfüllt sein.

## Empfohlene Reihenfolge

1. Destatis RSS als erste neue Nachrichtenquelle integrieren.
2. Lizenz- und Attributionsfelder im Datenmodell ergänzen.
3. European Commission Press Corner RSS/API integrieren.
4. GENESIS und Eurostat für data-driven Nachrichten ergänzen.
5. Für GovData und data.europa.eu einen automatischen License-Gate bauen.
6. Parallel ein Testangebot von dpa anfragen.
7. Reuters und AP erst nach einer groben Budgetentscheidung kontaktieren.
8. DW GNS nicht für den Deutschland-Launch einplanen, solange keine
   ausdrückliche territoriale Ausnahme vorliegt.
9. Wikinews DE nur als historisches Archiv betrachten.

## Verbindliche technische Grundregeln

Für jeden importierten Datensatz beziehungsweise Beitrag speichern:

- `source_name`
- `source_url`
- `original_title`
- `original_language`
- `publication_date`
- `retrieved_at`
- `licence`
- `licence_url`
- `copyright_holder`
- `is_translated`
- `is_ai_summarised`
- `changes_notice`
- `third_party_material_excluded`
- Revision beziehungsweise Version des Originals

Zusätzlich:

- Ohne erkannte und zulässige Lizenz keine automatische Veröffentlichung.
- Fotos, Videos, Logos und Marken niemals allein aufgrund der Textlizenz
  übernehmen.
- Übersetzung, Kürzung und LLM-Summarization sichtbar als Änderungen
  kennzeichnen.
- Originalquelle und Original-URL in App und API anzeigen.
- Für Telegram und Push mindestens Quelle und Link zum Original mitführen.
- Korrekturen, Löschungen, Embargos und `kill`-Meldungen der Quelle
  verarbeiten.
- Lizenztext beziehungsweise belastbaren Snapshot mit Abrufdatum
  archivieren.

---

## 1. Destatis RSS

### Bewertung

Beste offene Quelle für aktuelle offizielle statistische Nachrichten aus
Deutschland. Kann ohne Firma und ohne Vertrag verwendet werden.

### Zugriff

- Informationsseite:
  <https://www.destatis.de/DE/Service/RSS/RSS-Feed_artikel.html>
- RSS-Endpunkt:
  <https://www.destatis.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/Aktuell.xml?nn=3624>
- Registrierung: nicht erforderlich
- API-Key: nicht erforderlich
- Kosten: keine

Der Feed bietet täglich aktuelle Pressemitteilungen und ist ausdrücklich zur
maschinenlesbaren Weiterverarbeitung vorgesehen.

### Rechte

Offizielle Bedingungen:
<https://www.destatis.de/DE/Service/Impressum/copyright-allgemein.html>

Destatis erlaubt die kommerzielle und nichtkommerzielle Weiterverwendung,
Vervielfältigung und elektronische Verbreitung eigener Texte, Daten und
Grafiken. Eine individuelle Genehmigung ist nicht erforderlich.

Damit sind grundsätzlich möglich:

- RSS-Import
- Speicherung
- Übersetzung
- Kürzung
- LLM-Summarization
- Veröffentlichung in App und eigener API
- Telegram und Push

### Pflichten

- Destatis als Quelle nennen.
- Titel beziehungsweise genaue Fundstelle, URL und Abrufdatum angeben.
- Übersetzung, Kürzung, Berechnung oder sonstige Änderung kennzeichnen.
- Nicht den Eindruck erwecken, die russische Fassung sei eine offizielle
  Destatis-Übersetzung.

Empfohlene Angabe:

> Quelle: Statistisches Bundesamt (Destatis), „[Titel]“, [Datum], [URL],
> abgerufen am [Datum]. Nichtoffizielle russische Übersetzung und
> AI-Zusammenfassung; Text wurde gekürzt und verändert.

### Einschränkungen

- Die allgemeine Erlaubnis gilt nur für Inhalte, an denen Destatis die
  erforderlichen Rechte besitzt.
- Fotos und sonstige Drittinhalte nicht automatisch übernehmen.
- Abweichende Copyright-Hinweise einer konkreten Seite haben Vorrang.

### TODO

- [ ] Destatis RSS als neue Source implementieren.
- [ ] Nur Text, Metadaten und Original-URL importieren.
- [ ] Attributions- und Änderungsvermerk in allen Kanälen anzeigen.
- [ ] Bilder standardmäßig deaktivieren.

---

## 2. Destatis GENESIS-Online

### Bewertung

Beste offene Quelle für strukturierte deutsche Statistiken und eigene
data-driven Nachrichten.

### Zugriff

- Dokumentation:
  <https://www.destatis.de/DE/Service/OpenData/genesis-api-webservice-oberflaeche.html>
- Base URL:
  `https://genesis.destatis.de/genesisWS/rest/2020/`
- Daten sind grundsätzlich kostenlos.
- Für Produktionszugriff empfiehlt sich eine kostenlose Registrierung mit
  API-Token.
- Seit dem 30.06.2025 verwendet die API ausschließlich POST-Anfragen.

Zugangsdaten werden im Header übermittelt:

```text
Content-Type: application/x-www-form-urlencoded
username: API_TOKEN
password:
```

### Lizenz

<https://www.destatis.de/DE/Service/Impressum/copyright-genesis-online.html>

Lizenz:
`Datenlizenz Deutschland – Namensnennung – Version 2.0`

Erlaubt sind kommerzielle und nichtkommerzielle:

- Vervielfältigung
- Bearbeitung und Änderung
- Verbindung mit eigenen Daten
- Weitergabe an Dritte
- Integration in Produkte, Anwendungen und Geschäftsprozesse

### Attribution

> Datenquelle: Statistisches Bundesamt (Destatis), Genesis-Online,
> [Abrufdatum]; Datenlizenz by-2-0; eigene Berechnung/eigene Darstellung.

Bei LLM-Verarbeitung zusätzlich:

> Nichtoffizielle russische Interpretation und AI-Zusammenfassung; Daten und
> Text wurden verarbeitet und verändert.

### TODO

- [ ] Kostenloses GENESIS-Konto registrieren.
- [ ] API-Token erzeugen und ausschließlich im Secret-Management speichern.
- [ ] Relevante Tabellen und Aktualisierungsintervalle festlegen.
- [ ] Dataset-Code, Filter, URI, Abrufdatum und Lizenz speichern.
- [ ] Eigene Berechnungen und LLM-Interpretationen deutlich kennzeichnen.

---

## 3. European Commission Press Corner

### Bewertung

Geeignet für offizielle EU-Nachrichten. Keine Firma, Registrierung oder
schriftliche Lizenz erforderlich, sofern der konkrete Inhalt der EU gehört.

### Zugriff

- Portal:
  <https://ec.europa.eu/commission/presscorner/home/en>
- RSS:
  <https://ec.europa.eu/commission/presscorner/api/rss?language=en&pagesize=20>

Öffentlich erreichbare Endpunkte:

```text
GET /commission/presscorner/api/latestnews
GET /commission/presscorner/api/search
GET /commission/presscorner/api/documents
GET /commission/presscorner/api/rss
```

- API-Key: nicht erforderlich
- Registrierung: für RSS/JSON nicht erforderlich
- EU Login: nur für personalisierte Alerts erforderlich
- Kosten: keine

Die JSON-Endpunkte werden vom offiziellen Frontend verwendet, besitzen jedoch
keinen veröffentlichten versionierten API-Vertrag. Für Production sollte RSS
als Discovery-Kanal verwendet und die JSON-Schemaänderung überwacht werden.

### Lizenz

<https://commission.europa.eu/legal-notice_en>

EU-owned content steht grundsätzlich unter CC BY 4.0. Wiederverwendung,
kommerzielle Nutzung und Bearbeitung sind erlaubt, wenn die Quelle genannt und
Änderungen angegeben werden.

### Empfohlene Attribution

> Источник: European Commission, Press Corner, „[Originaltitel]“, [Datum],
> [URL]. © European Union. Неофициальный перевод и AI-суммаризация:
> [название приложения]. Текст сокращён и изменён; при расхождениях действует
> оригинал.

### Einschränkungen

- Drittwerke und Inhalte mit eigenem Copyright nicht automatisch übernehmen.
- Fotos mit erkennbaren Personen gesondert prüfen.
- Logos, Namen und Marken sind nicht durch die allgemeine CC-BY-Erlaubnis
  freigegeben.
- Das App-Design darf keine offizielle Partnerschaft mit der EU suggerieren.
- Der individuelle Copyright-Hinweis hat Vorrang.

### TODO

- [ ] Press Corner RSS implementieren.
- [ ] Dokumentdetails über den offiziellen JSON-Endpunkt laden.
- [ ] Nur EU-owned Textinhalte automatisch zulassen.
- [ ] Bilder und Anhänge standardmäßig ausschließen.
- [ ] Attribution und Change Notice für alle Kanäle implementieren.
- [ ] Schema-Monitoring und RSS-Fallback einrichten.

---

## 4. Eurostat

### Bewertung

Sehr gut für Wirtschafts-, Bevölkerungs-, Arbeitsmarkt- und Sozialdaten.
Keine Firma, Registrierung oder schriftliche Lizenz erforderlich.

### Zugriff

- API-Dokumentation:
  <https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-getting-started/api>
- Copyright:
  <https://ec.europa.eu/eurostat/en/help/copyright-notice>

Verfügbar sind:

- JSON-stat API
- SDMX 2.1
- SDMX 3.0
- Bulk Download
- Data Browser

Beispiel:

```text
GET https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/{DATASET_CODE}
```

Öffentliche API-Aufrufe benötigen keinen Key. Automatisierte Extraction-Calls
sollen nacheinander und nicht parallel ausgeführt werden.

### Rechte

Die kommerzielle und nichtkommerzielle Wiederverwendung statistischer Daten,
Metadaten, Veröffentlichungen und eigener redaktioneller Inhalte von Eurostat
ist mit Quellenangabe erlaubt. Eine schriftliche Lizenz ist nicht erforderlich.

### Attribution

Für Datasets:

> Source: [Eurostat DOI oder Datacode-Link], [Abrufdatum].

Für Übersetzungen verlangt Eurostat insbesondere:

- Titel und Sprache des Originals
- Eurostat/EU als ursprüngliche Quelle
- Name beziehungsweise Bezeichnung des Übersetzers
- Hinweis, dass der Übersetzer für die Übersetzung verantwortlich ist
- Hinweis, dass bei Abweichungen das Original maßgeblich ist
- Kennzeichnung von Daten- und Textänderungen

### Einschränkungen

- Drittanbieterfotos und -illustrationen sind ausgeschlossen.
- Logos und Marken sind ausgeschlossen.
- Einzelne Dokumente können abweichende Copyright-Hinweise haben.
- Bestimmte internationale und Handelsdaten sind von kommerzieller
  Weiterverwendung ausgenommen.

### TODO

- [ ] Relevante Dataset-Codes auswählen.
- [ ] Sequenziellen API-Client mit Cache implementieren.
- [ ] DOI/Datacode, Filter und Abrufdatum speichern.
- [ ] Eurostat Translation Disclaimer im Frontend ergänzen.
- [ ] Individuelle Ausnahmen automatisch beziehungsweise manuell prüfen.

---

## 5. GovData / data.gov.de

### Bewertung

Geeignet als Discovery-Katalog für deutsche Verwaltungsdaten, nicht als
einheitlich lizenzierte Nachrichtenquelle.

### Zugriff

- CKAN:
  <https://www.govdata.de/ckan/api>
- Lizenzinformationen:
  <https://www.govdata.de/informationen/lizenzen>
- SPARQL:
  <https://www.govdata.de/sparql>

Lesender Zugriff ist ohne Registrierung und API-Key möglich.

### Lizenzprinzip

GovData hostet nicht zwingend die eigentlichen Daten. Der jeweilige Anbieter
bestimmt die Nutzungsbedingungen.

Automatisch akzeptierbare Allowlist:

- CC0
- CC BY
- DL-DE Zero 2.0
- DL-DE BY 2.0

Automatisch blockieren:

- keine Lizenz
- unbekannte oder nicht maschinenlesbare Lizenz
- NC
- ND
- individuelle restriktive Bedingungen

Die Lizenz muss pro `distribution/resource` geprüft werden, nicht nur auf
Dataset-Ebene.

### TODO

- [ ] CKAN/DCAT-Importer mit Pagination und Cache erstellen.
- [ ] License-Allowlist implementieren.
- [ ] Publisher, Dataset-URI, Resource-URI und License-URI speichern.
- [ ] Daten beim ursprünglichen Anbieter laden.
- [ ] Unbekannte Lizenzen zur manuellen Prüfung senden.
- [ ] Request-Frequenz begrenzen.

---

## 6. data.europa.eu

### Bewertung

EU-weiter Discovery-Katalog. Keine Firma, Registrierung oder API-Key für
lesenden Zugriff erforderlich. Die Lizenz jedes Datasets muss separat geprüft
werden.

### Zugriff

- API-Katalog:
  <https://data.europa.eu/en/which-apis-are-available-and-where-can-i-find-information-about-them>
- Dataset RSS:
  <https://data.europa.eu/api/hub/search/en/feeds/datasets.rss>
- Dataset Atom:
  <https://data.europa.eu/api/hub/search/en/feeds/datasets.atom>
- SPARQL:
  <https://data.europa.eu/data/sparql?locale=en>

Verfügbar sind:

- Search/CKAN API
- RSS/Atom
- SPARQL
- Registry Read API

### Lizenzprinzip

- Metadaten des Portals: CC0
- Redaktionsinhalte des Portals: CC BY 4.0
- Inhalte der gefundenen Datasets: jeweilige Lizenz des Publishers

Das Portal indexiert ausdrücklich auch Datasets mit nichtkommerziellen
Lizenzen. Daher bedeutet das Vorhandensein auf data.europa.eu nicht, dass eine
kommerzielle Nutzung erlaubt ist.

### TODO

- [ ] Search/RSS/SPARQL als Discovery integrieren.
- [ ] Pro Distribution Lizenz und Rights-Felder prüfen.
- [ ] Dieselbe Allowlist wie für GovData anwenden.
- [ ] NC, ND und unbekannte Lizenzen blockieren.
- [ ] ShareAlike-Auswirkungen auf abgeleitete Datasets prüfen.

---

## 7. Wikinews DE

### Bewertung

Kein aktueller Nachrichtenanbieter mehr. Das deutschsprachige Wikinews wurde
am 04.05.2026 geschlossen und ist nur als Archiv geeignet.

### Zugriff

- Archiv:
  <https://de.wikinews.org/wiki/Hauptseite>
- API:
  <https://de.wikinews.org/w/api.php>
- Lizenz:
  <https://de.wikinews.org/wiki/Wikinews:Lizenzbestimmungen>

Lesender API-Zugriff benötigt keine Registrierung und keinen Key.

### Lizenz

Texte stehen unter CC BY 2.5. Erlaubt sind:

- kommerzielle Nutzung
- Speicherung
- Übersetzung
- Bearbeitung
- LLM-Summarization
- Veröffentlichung über App/API/Telegram/push

Erforderlich sind die Zuschreibung zu `de.wikinews.org` und der Hinweis auf
CC BY 2.5.

### Einschränkungen

- Nach dem 04.05.2026 erscheinen keine neuen Artikel.
- Bild- und Dateirechte müssen pro Datei geprüft werden.
- Wikinews ist eine eingetragene Marke.

### TODO

- [ ] Nicht als aktuelle Produktionsquelle einplanen.
- [ ] Falls benötigt, separaten Archivmodus vorsehen.
- [ ] Attribution und Lizenzlink pro historischem Artikel anzeigen.
- [ ] Medien nur nach separater Lizenzprüfung übernehmen.

---

## 8. Deutsche Welle / German News Service

### Bewertung

Ohne schriftliche Ausnahme nicht für den Deutschland-Launch einplanen. Die
offizielle GNS-Seite erklärt, dass das zusätzliche Angebot in
deutschsprachigen europäischen Ländern nicht verfügbar ist.

### Zugriff

- GNS:
  <https://www.dw.com/en/about-gns/a-65945240>
- GNS-Bedingungen:
  <https://www.dw.com/en/general-terms-and-conditions-german-news-service/a-18507160>
- Licensing:
  <https://corporate.dw.com/en/licensing-dw-content/a-77070261>

Angeboten werden:

- dpa agency material über GNS
- DW Content Box
- Video Player
- RSS Import

### Firma

Die Seiten richten sich an Journalisten, Medienprofis, Website-Betreiber,
Medienunternehmen, Institutionen und professionelle Partner. Eine GmbH wird
nicht ausdrücklich verlangt. Ob ein nicht registriertes Projekt oder
Einzelunternehmen akzeptiert wird, muss DW schriftlich bestätigen.

### Wichtige Einschränkungen

- Das kostenlose Angebot ist für deutschsprachige europäische Länder
  ausdrücklich ausgeschlossen.
- DW-RSS-Bedingungen sind an die im Antrag genannte Website gebunden.
- DW-Content darf nach den allgemeinen RSS-Bedingungen nicht ohne zusätzliche
  Zustimmung gekürzt oder verändert werden.
- Übersetzung, LLM-Summarization, eigene API, Telegram und Push sind nicht
  pauschal freigegeben.

### TODO

- [ ] DW schriftlich fragen, ob ein russischsprachiges Angebot mit Betreiber in
      Deutschland zugelassen werden kann.
- [ ] Alle Kanäle und den vollständigen AI-Workflow beschreiben.
- [ ] Bevorzugt eine fertige russische GNS-Fassung anfragen.
- [ ] Ohne schriftliche Ausnahme nicht implementieren.

Kontakt: `gns@dw.com`

---

## 9. dpa

### Bewertung

Wahrscheinlich der passendste professionelle Anbieter für Deutschland. Für
reguläre News ist ein kostenpflichtiger Vertrag erforderlich.

### Produkte

- dpa-WebLines:
  <https://www.dpa.com/de/inhalte-websites-apps>
- dpa international:
  <https://www.dpa.com/en/international-news>
- dpa-iq:
  <https://www.dpa.com/de/dpa-iq>

dpa-WebLines bietet für Websites und Apps vorbereitete News-Feeds. dpa-iq ist
für RAG, strukturierte Antworten und AI-Workflows ausgelegt.

### Firma

dpa erklärt, dass grundsätzlich Unternehmen Kunden werden können und keine
Nachrichten an Privatpersonen verkauft werden. Die Formulare verlangen ein
Unternehmen. Ob ein Einzelunternehmen ohne Handelsregistereintrag akzeptiert
wird, muss dpa bestätigen.

Eine Anfrage als „Projekt in Gründung“ kann bereits jetzt gestellt werden.
Spätestens für den Vertrag wird ein definierter Geschäftspartner benötigt.

### Antrag

Angeben:

- Name und Rolle
- Projekt beziehungsweise Firma
- Land
- E-Mail und Telefon
- Produkt-URL oder Prototyp
- Zielgruppe
- erwarteter Traffic
- Plattformen
- gewünschte Sprachen
- App/API/Telegram/push
- Speicherfristen
- OpenAI beziehungsweise anderer LLM-Anbieter
- Übersetzung und Summarization
- gewünschter Testzeitraum

### Vertraglich ausdrücklich verlangen

- DE/EN nach RU übersetzen
- LLM/RAG/Summarization
- Übermittlung an den konkret genannten LLM-Anbieter
- Speicherung von Original und Metadaten
- Veröffentlichung in App, eigener API, Telegram und Push
- zulässige Bearbeitung
- Attribution
- Archivdauer
- Territorium
- Traffic und Nutzerzahl
- Weitergabe an Endnutzer
- Korrektur-, Update- und Kill-Prozess

### TODO

- [ ] Kostenlosen Test beziehungsweise dpa-iq Private Preview anfragen.
- [ ] Budgetangebot einholen.
- [ ] Einzelunternehmen beziehungsweise Projekt in Gründung als
      Vertragspartner klären.
- [ ] AI- und Multichannel-Rechte ausdrücklich in den Vertrag aufnehmen.

Kontakte:

- `sales@dpa.com`
- `internationalsales@dpa.com`

---

## 10. Reuters

### Bewertung

Technisch sehr geeignet, aber voraussichtlich teuer. Individueller
kommerzieller Vertrag ist erforderlich.

### Produkte

- Reuters Connect:
  <https://reutersagency.com/content-delivery-platforms/reuters-connect/>
- Reuters API/MCP:
  <https://reutersagency.com/content-delivery-platforms/api-integrations/>
- Antrag:
  <https://reutersagency.com/license-reuters-content/>

### Firma

Das Formular verlangt Company/Organization, Company Website, Work Email und
Business Phone. Ob ein Einzelunternehmen oder Projekt vor Registrierung
akzeptiert wird, ist öffentlich nicht zugesichert.

### Rechte

Preis, Inhalte, Speicherung, Bearbeitung und Kanäle werden individuell
vereinbart. Das Vorhandensein von Reuters API, MCP oder internen AI-Tools
erteilt nicht automatisch das Recht auf externe LLM-Verarbeitung.

Vertraglich klären:

- Übersetzung ins Russische
- LLM-Summarization
- externer AI-Provider
- App/API/Telegram/push
- zulässige Speicherung und Archivierung
- Attribution, Dateline und Byline
- Partner-Content
- Korrekturen und Rückruf

### TODO

- [ ] Erst nach Budgetentscheidung Reuters Sales kontaktieren.
- [ ] Company Website beziehungsweise funktionsfähigen Prototyp vorbereiten.
- [ ] Bespoke-Angebot mit allen Kanälen anfordern.
- [ ] Reuters- und Partner-Content getrennt lizenzieren.

---

## 11. Associated Press

### Bewertung

Geeignet über AP Media API und gegebenenfalls AP Intelligence. Individuelle
kostenpflichtige Lizenz erforderlich.

### Produkte

- AP Media API:
  <https://developer.ap.org/ap-media-api/>
- API Getting Started:
  <https://api.ap.org/media/v/docs/Getting_Started_API.htm>
- AP Intelligence:
  <https://www.ap.org/intelligence/>
- Sales:
  <https://www.ap.org/contact-us/contact-sales/>

### Firma

Das Formular verlangt Company, nennt aber Freelancer als mögliche Industry.
Eine Anfrage ist deshalb auch als Freelancer realistisch. Ob ein noch nicht
registriertes Projekt akzeptiert wird, muss AP bestätigen.

### Zugriff

Nach Vertrag erhält der Kunde:

- API-Key
- Product IDs
- Quotas
- vertraglich freigegebene Content-Pläne

Jedes Item kann eigene Einschränkungen enthalten:

- kein Archiv
- Ablaufdatum
- begrenztes Territorium
- Pflicht-Credits
- Drittanbieterrechte
- Korrektur oder Kill

### Vertraglich klären

- Übersetzung
- LLM/RAG/Summarization
- Training beziehungsweise Fine-Tuning, falls geplant
- Speicherung
- eigene API
- App/Telegram/push
- Sublicensing
- Item-Level-Rights-Processing

### TODO

- [ ] AP Sales zu Enterprise Text Subscription und AP Intelligence anfragen.
- [ ] Freelancer/Einzelunternehmen als Vertragspartner bestätigen lassen.
- [ ] AI- und Multichannel-Nutzung ausdrücklich aufnehmen.
- [ ] RightsML/ODRL, `pubstatus`, `expires`, corrections und kills technisch
      verarbeiten.

---

## Entscheidungsvorschlag

### Sofort umsetzbar

- Destatis RSS
- Destatis GENESIS
- European Commission Press Corner
- Eurostat
- GovData und data.europa.eu mit strengem License-Gate

### Nur Archiv

- Wikinews DE

### Nur nach schriftlicher Zustimmung beziehungsweise Vertrag

- DW/GNS
- dpa
- Reuters
- AP

### Priorität für bezahlte Quelle

1. dpa
2. Reuters
3. AP

dpa passt inhaltlich und geografisch am besten zu einer
russischsprachigen Nachrichtenanwendung für Menschen in Deutschland.
