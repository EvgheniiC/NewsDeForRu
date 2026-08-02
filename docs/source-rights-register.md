# Quellen- und Lizenzregister

Stand der Prüfung: 02.08.2026

> Arbeitsdokument, keine Rechtsberatung. Eine Quelle gilt erst dann als für die
> Produktion freigegeben, wenn der konkrete Nutzungsumfang schriftlich bestätigt
> oder durch eine deutsche Fachkanzlei belastbar bewertet wurde.

## Geprüfter Nutzungsumfang

Die Anwendung ruft RSS-Feeds automatisiert ab und speichert mindestens GUID,
Überschrift, Beschreibung/Teaser, Artikel-URL, Veröffentlichungszeitpunkt und
gegebenenfalls eine Bild-URL. Überschrift und Beschreibung werden automatisiert
gefiltert, geclustert und an ein KI-Modell zur Erstellung russischsprachiger
Zusammenfassungen übermittelt. Die Ergebnisse können in App/API, Telegram und
Push-Benachrichtigungen veröffentlicht werden. Originalartikel werden verlinkt.
Herausgeberbilder werden derzeit nicht in `processed_news` übernommen.

Technische Referenzen:

- `backend/app/services/rss_sources.py`
- `backend/app/services/rss_entry_normalization.py`
- `backend/app/services/rss_ingestion_service.py`
- `backend/app/services/pipeline_service.py`
- `backend/app/services/telegram_notifier.py`
- `backend/app/services/push_notifier.py`
- `backend/app/models/news.py`

## Freigabestatus

| Quelle | Konfigurierter Feed | Status | Produktionsentscheidung |
| --- | --- | --- | --- |
| Tagesschau | `https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml` | Nicht freigegeben | Deaktivieren, bis eine schriftliche Erlaubnis vorliegt |
| DER SPIEGEL | `https://www.spiegel.de/schlagzeilen/index.rss` | Nicht freigegeben | Deaktivieren, bis eine schriftliche Lizenz vorliegt |
| DIE ZEIT | `https://newsfeed.zeit.de/news/index` | Unklar/nicht freigegeben | Deaktivieren, bis der Widerspruch zwischen älterem RSS-Hinweis und aktuellem Nutzungsvorbehalt schriftlich geklärt ist |
| ZDF | `https://www.zdfheute.de/rss/zdf/nachrichten` | Nicht freigegeben | Deaktivieren, bis Feed-Autorisierung und Nutzungsumfang schriftlich bestätigt sind |
| WELT | `https://www.welt.de/feeds/latest.rss` | Nicht freigegeben | Deaktivieren, bis Syndication die konkrete Nutzung schriftlich genehmigt |
| Destatis | `https://www.destatis.de/SiteGlobals/Functions/RSSFeed/DE/RSSNewsfeed/Aktuell.xml?nn=3624` | Freigegeben, Text-only | Quellenangabe, Fundstelle, Abrufdatum und Änderungsvermerk ausgeben |
| European Commission Press Corner | `https://ec.europa.eu/commission/presscorner/api/rss?language=en&pagesize=20` | Freigegeben, EU-owned Text-only | CC BY 4.0; Drittwerke, Medien, Logos und abweichende Hinweise ausschließen |
| Destatis GENESIS-Online | konfigurierbare Tabellen-API | Freigegeben, Allowlist | DL-DE-BY-2.0; Dataset-Code, Abrufdatum und eigene Verarbeitung angeben |
| Eurostat | konfigurierbare JSON-stat API | Freigegeben, Allowlist | Copyright notice und Ausnahmen pro Dataset beachten; sequenziell abrufen |

`Nicht freigegeben` bedeutet nicht, dass jede Nutzung zwingend rechtswidrig ist.
Es bedeutet, dass die für dieses Produkt erforderlichen Rechte durch die
geprüften offiziellen Informationen nicht eindeutig belegt sind.

Die vier offenen Quellen werden technisch fail-closed betrieben: RSS-Quellen
müssen in `RSS_ENABLED_SOURCE_KEYS`, Statistik-Datasets in
`GENESIS_DATASET_CODES` beziehungsweise `EUROSTAT_DATASET_CODES` stehen.
Alle Importe sind Text-only und benötigen verifizierte Lizenzmetadaten, bevor
automatische oder manuelle Veröffentlichung möglich ist.

## Tagesschau

- Betreiber: ARD-aktuell beim Norddeutschen Rundfunk.
- Offizieller Feed „Alle Meldungen“:
  <https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml>
- Offizielle RSS-Übersicht:
  <https://www.tagesschau.de/infoservices/rssfeeds>
- Spezifische RSS-Bedingungen:
  <https://www.tagesschau.de/rssfeed-ts-104.html>
- Stand der verlinkten RSS-Bedingungen: 26.11.2014; abgerufen am 02.08.2026.
- Kernaussage: Nutzung ausschließlich für nicht-kommerzielle
  Internet-Angebote; Weitergabe an Dritte und Archivierung sind untersagt.
  Quelle und direkter Link zum Original sind erforderlich. Die Erlaubnis kann
  jederzeit widerrufen werden.
- Aktueller maschinenlesbarer Vorbehalt:
  <https://www.tagesschau.de/robots.txt>, Stand im Dokument 19.05.2026,
  abgerufen am 02.08.2026. Der Vorbehalt untersagt kommerzielles Text- und
  Data-Mining sowie KI-Training ohne vorherige schriftliche Zustimmung. RAG
  beziehungsweise Grounding wird nur unter Einhaltung der technischen Regeln
  und mit Quellenangabe ausgenommen.
- Kontakt: `webmaster@tagesschau.de`; Impressum:
  <https://www.tagesschau.de/impressum>.
- Erforderlich zu klären: kommerzielle App/API, Speicherung, Übersetzung,
  KI-Zusammenfassung, Übermittlung an einen KI-Dienst, Telegram, Push,
  zulässige Felder, Aufbewahrungsdauer und Widerruf.
- Risikobewertung: hoch. Der aktuelle Betrieb speichert RSS-Inhalte und gibt
  verarbeitete Inhalte an Dritte weiter; beides ist vom veröffentlichten
  Standardumfang nicht gedeckt.

## DER SPIEGEL

- Allgemeine Nutzungsbedingungen:
  <https://www.spiegel.de/nutzungsbedingungen>
- Version: 2.3.0 vom 11.04.2025; abgerufen am 02.08.2026.
- Kernaussage: Untersagt sind unter anderem die nicht-private Weitergabe und
  Speicherung, elektronische Archive, automatisiertes Auslesen und Analysieren,
  Nutzung für RSS-Feeds, Snippets sowie Bearbeitung von Texten. Weitere
  Nutzungen benötigen vorherige Zustimmung.
- Syndication und Lizenzanfrage:
  <https://gruppe.spiegel.de/syndication/anfrage>
- Kernaussage der Syndication-AGB: Nutzung erst nach schriftlicher
  Lizenzbestätigung; Übersetzung und Bearbeitung benötigen eine gesonderte
  Vereinbarung; KI-Nutzung ist ohne abweichende Vereinbarung unzulässig.
- Aktueller maschinenlesbarer Vorbehalt:
  <https://www.spiegel.de/robots.txt>, abgerufen am 02.08.2026. Automatisches
  Sammeln und kommerzielles Text- und Data-Mining sind ohne ausdrückliche
  Erlaubnis untersagt.
- Kontakt: `syndication@spiegel.de`, Telefon laut Nutzungsbedingungen
  `+49 40 3007-3540`.
- Erforderlich zu klären: sämtliche oben beschriebenen Nutzungsarten,
  insbesondere Übersetzung, KI-Verarbeitung, Speicherung, Snippets und
  Mehrkanalveröffentlichung.
- Risikobewertung: sehr hoch. Die konkret eingesetzten Verarbeitungsschritte
  werden in den Bedingungen ausdrücklich erfasst.

## DIE ZEIT

- RSS-/Zitat-Hinweis:
  <https://blog.zeit.de/zeitansage/2013/04/17/bitte-zitieren-sie-uns-gerne_1246>
- Stand des Hinweises: 17.04.2013; abgerufen am 02.08.2026.
- Kernaussage: Kurze Auszüge aus redaktionellen Texten, Content-API und
  RSS-Feeds dürfen nach diesem Hinweis in Online-Veröffentlichungen mit
  Quellenangabe und direktem Link verwendet werden. Für Werbung sowie größere
  Textpassagen oder ganze Texte bei kommerzieller Nutzung soll angefragt werden.
- Aktueller maschinenlesbarer Vorbehalt:
  <https://www.zeit.de/robots.txt>, abgerufen am 02.08.2026. Er untersagt
  automatisiertes Sammeln/Mining und kommerzielles Text- und Data-Mining ohne
  ausdrückliche Erlaubnis und sperrt zahlreiche KI-Crawler.
- Kontakte: `zitat@zeit.de` (älterer RSS-/Zitat-Hinweis) und
  `online-syndication@zeit.de` (aktueller robots.txt).
- Erforderlich zu klären: Ob der Hinweis von 2013 noch gilt und ob er
  Speicherung, Übersetzung, KI-Zusammenfassung, externe KI-Übermittlung,
  Telegram, Push und kommerziellen App-Betrieb umfasst.
- Risikobewertung: hoch. Ein älterer großzügiger RSS-Hinweis reicht angesichts
  des aktuellen ausdrücklichen Nutzungsvorbehalts nicht als belastbarer
  Produktionsnachweis.

## ZDF

- Offizieller aktueller Feed:
  <https://www.zdfheute.de/rss/zdf/nachrichten>. Die am 02.08.2026
  abgerufene Feed-Ausgabe bezeichnet diese URL selbst als kanonische
  `rel="self"`-Adresse.
- Allgemeine Nutzungsbedingungen:
  <https://www.zdf.de/mt2025-nutzungsbedingungen-100>
- Abgerufen am 02.08.2026.
- Kernaussage: ZDF-Online-Inhalte sind urheberrechtlich geschützt.
  Vervielfältigung, Änderung, Verbreitung oder Speicherung von Informationen,
  Daten, Texten und Textteilen bedürfen vorheriger schriftlicher Zustimmung.
  Das Online-Angebot darf grundsätzlich nur privat und nichtkommerziell genutzt
  werden, soweit keine spezielle Funktion eine abweichende Nutzung erlaubt.
- Es wurde keine aktuelle offizielle Seite gefunden, die den verwendeten
  Nachrichten-Feed und den hier geprüften kommerziellen Aggregationsumfang
  ausdrücklich freigibt.
- robots.txt: <https://www.zdfheute.de/robots.txt>, abgerufen am 02.08.2026. Er
  enthält Sperren für benannte KI-/Crawler-User-Agents; ein allgemeiner
  RSS-Nutzungsumfang wird dort nicht erteilt.
- Geschäftskontakt: `info@zdf.de`; Kontaktseite:
  <https://www.zdf.de/mt2025-kontakt-100>. Für Presseportal-Material nennt ZDF
  außerdem `pressefoto@zdf.de`; diese Bedingungen sind keine Freigabe für den
  Nachrichten-RSS-Feed.
- Erforderlich zu klären: Echtheit/Weiterbetrieb des Feed-Endpunkts,
  kommerzieller Abruf, Speicherung, Übersetzung, KI-Verarbeitung, Telegram,
  Push, zulässige Felder und Löschfristen.
- Risikobewertung: sehr hoch. Es fehlt eine spezielle RSS-Erlaubnis, während
  die allgemeinen Bedingungen die relevanten Handlungen zustimmungspflichtig
  machen.

## WELT

- Offizielle RSS-Seite und RSS-Bedingungen:
  <https://www.welt.de/services/article157826206/RSS-Feed-Abonnieren-Sie-die-WELT-auf-Ihrem-Feedreader.html>
- Abgerufen am 02.08.2026.
- Kernaussage: Für private Nutzung sind Überschriften und Teaser zusammen mit
  dem Link zum Original gestattet. Bilder/Videos sind nicht umfasst;
  Weitergabe an Dritte ist untersagt. Für die Integration auf kommerziell
  betriebenen Webseiten muss Syndication unter Angabe von URL,
  Ansprechpartner, Zweck und monatlichem Traffic kontaktiert werden. Die
  Erlaubnis kann widerrufen und der Feed geändert oder eingestellt werden.
- Aktueller robots.txt:
  <https://www.welt.de/robots.txt>, abgerufen am 02.08.2026. Viele
  KI-/Datensammler sind vollständig gesperrt; der allgemeine User-Agent darf
  nur außerhalb der aufgeführten Pfade zugreifen.
- Kontakt: `syndication@welt.de`.
- Erforderlich zu klären: App/API statt nur Webseite, Speicherung,
  Übersetzung, KI-Zusammenfassung, Übermittlung an einen KI-Dienst, Telegram,
  Push, zulässige Felder, Traffic, Laufzeit und Widerruf.
- Risikobewertung: hoch. Kommerzielle Nutzung ist möglicherweise
  lizenzierbar, aber noch nicht genehmigt.

## Mindestinhalt einer schriftlichen Freigabe

Die Antwort des Rechteinhabers muss den Betreiber und mindestens folgende
Punkte eindeutig benennen:

1. kommerzielle Aggregation in Web-, Android- und iOS-App sowie API;
2. automatischer RSS-Abruf mit gewünschter Frequenz;
3. Speicherung von Überschrift, Teaser, URL, Datum und technischen Metadaten;
4. erlaubte Aufbewahrungsdauer und Löschpflichten;
5. Übersetzung und KI-gestützte Zusammenfassung;
6. Übermittlung der Feed-Texte an den konkret eingesetzten KI-Anbieter;
7. Veröffentlichung eigener russischer Zusammenfassungen in App und Telegram;
8. Verwendung eigener Kurztexte in Push-Benachrichtigungen;
9. Quellenangabe, Linkgestaltung, Marken- und Logoanforderungen;
10. zulässige Nutzung von Bildern oder ausdrücklicher Ausschluss;
11. Gebiete, Plattformen, Laufzeit, Vergütung und Traffic-Grenzen;
12. Änderungs-, Widerrufs-, Korrektur- und Löschverfahren.

Schweigen, der bloße technische Zugriff auf einen Feed oder eine allgemeine
RSS-Erklärung gelten nicht als Freigabe des gesamten Produktumfangs.

## Wiederholungsprüfung

- Verantwortlich: vor Produktionsfreigabe schriftlich festlegen.
- Turnus: mindestens vierteljährlich und zusätzlich vor jedem Release, das
  Abruf, Speicherung, KI-Anbieter, Veröffentlichungswege oder Datenfelder
  ändert.
- Pro Prüfung archivieren: Datum, Prüfer, URL, Seitenversion/Stand,
  PDF/Screenshot oder unveränderbare Kopie, robots.txt, Feed-Header,
  Lizenzkorrespondenz und resultierende Entscheidung.
- Änderungen mit engeren Bedingungen führen automatisch zum Status
  `gesperrt`, bis Product Owner und juristische Beratung neu freigeben.
- Lizenzablauf oder Widerruf führt zur sofortigen Deaktivierung des Abrufs und
  zur Ausführung der vereinbarten Löschpflichten.

## Offene Nachweise

- [ ] Schriftliche Freigabe/Lizenz Tagesschau
- [ ] Schriftliche Freigabe/Lizenz DER SPIEGEL
- [ ] Schriftliche Freigabe/Lizenz DIE ZEIT
- [ ] Schriftliche Freigabe/Lizenz ZDF
- [ ] Schriftliche Freigabe/Lizenz WELT
- [ ] Betreiber, Produkt-URLs und erwartete monatliche Abrufe/Traffic ergänzt
- [ ] Antworten und Lizenzfassungen revisionssicher archiviert
- [ ] Juristische Bewertung der erlaubten Snippets und eigenen
      Zusammenfassungen dokumentiert
- [ ] Technische Quellen-Deaktivierung bis zur jeweiligen Freigabe geprüft
