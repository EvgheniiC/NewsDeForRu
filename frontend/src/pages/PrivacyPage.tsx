import { AnalyticsRevokeButton } from "../components/AnalyticsRevokeButton";
import { LegalOperatorBlock } from "../components/LegalOperatorBlock";
import { getLegalConfig } from "../config/legal";

export function PrivacyPage(): JSX.Element {
  const legal = getLegalConfig();
  const contact: string = legal.contactEmail || "siehe Impressum";

  return (
    <section className="legal-page">
      <h1>Datenschutzerklärung / Конфиденциальность</h1>
      <p className="muted">
        Stand: Juni 2026 · Anwendung: DSGVO, TTDSG · Dienst:{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>
      </p>
      <p className="legal-disclaimer">
        Technischer Entwurf für einen privaten Betreiber in Deutschland. Keine Rechtsberatung —
        bei Bedarf Anwalt hinzuziehen.
      </p>

      <h2>1. Verantwortlicher / Оператор</h2>
      <LegalOperatorBlock />
      <p>
        Datenschutzanfragen:{" "}
        {legal.contactEmail ? (
          <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
        ) : (
          contact
        )}
      </p>

      <h2>2. Überblick / Кратко</h2>
      <ul>
        <li>
          <strong>Лента без регистрации</strong> — чтение новостей; технические логи на сервере в{" "}
          {legal.hostingCountry}.
        </li>
        <li>
          <strong>Опциональный аккаунт</strong> — e-mail, хеш пароля, JWT в localStorage (
          <code>newsfr.auth.*</code>).
        </li>
        <li>
          <strong>Аналитика использования</strong> — только после согласия в баннере (псевдонимные ID,
          события на <code>/engagement/events</code>).
        </li>
        <li>
          <strong>Пайплайн</strong> — RSS, БД на сервере в DE; обработка текстов через OpenAI (США);
          уведомления в Telegram при включённой настройке на сервере.
        </li>
      </ul>

      <h2>3. Zwecke und Rechtsgrundlagen (Art. 6 DSGVO)</h2>
      <div className="legal-table-wrap">
        <table className="legal-table">
          <thead>
            <tr>
              <th>Daten</th>
              <th>Zweck</th>
              <th>Rechtsgrundlage</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Server-Logs (Zeit, Pfad, Status, Fehler; keine Passwörter/Keys)</td>
              <td>Betrieb, Sicherheit</td>
              <td>Art. 6 Abs. 1 lit. f</td>
            </tr>
            <tr>
              <td>RSS-Rohdaten, verarbeitete Artikel, Embeddings in DB (DE)</td>
              <td>News-Pipeline, Veröffentlichung</td>
              <td>Art. 6 Abs. 1 lit. f</td>
            </tr>
            <tr>
              <td>Artikeltexte an OpenAI API (gpt-4o-mini, api.openai.com)</td>
              <td>Zusammenfassung, Übersetzung, Bewertung</td>
              <td>Art. 6 Abs. 1 lit. f; Drittland USA — SCC der Anbieter</td>
            </tr>
            <tr>
              <td>Telegram Bot API (Titel/Link bei Autopublish)</td>
              <td>Kanal-Benachrichtigungen</td>
              <td>Art. 6 Abs. 1 lit. f</td>
            </tr>
            <tr>
              <td>E-Mail, Passwort-Hash, Refresh-Token (DB DE)</td>
              <td>Konto, Login, Passwort-Reset</td>
              <td>Art. 6 Abs. 1 lit. b</td>
            </tr>
            <tr>
              <td>SMTP (mail.gmx.net) — Reset-Link</td>
              <td>Transaktions-E-Mail</td>
              <td>Art. 6 Abs. 1 lit. b</td>
            </tr>
            <tr>
              <td>
                Pseudonyme IDs (<code>nga_anonymous_user_id</code>, <code>nga_session_id</code>),
                Engagement-Events
              </td>
              <td>Nutzungsstatistik (welche Artikel genutzt werden)</td>
              <td>Art. 6 Abs. 1 lit. a (Einwilligung, Banner)</td>
            </tr>
            <tr>
              <td>JWT in localStorage</td>
              <td>Sitzung nach Login</td>
              <td>Art. 6 Abs. 1 lit. b / f (technisch erforderlich)</td>
            </tr>
            <tr>
              <td>Lokal „nützlich“ (<code>nga_useful_*</code>)</td>
              <td>Anzeige im Browser; Sync nur mit Analytics-Einwilligung</td>
              <td>Einwilligung bzw. lokal ohne Server</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>4. Speicherdauer / Сроки</h2>
      <ul>
        <li>Server-Logs: bis zu 90 Tage (je nach Hoster-Rotation).</li>
        <li>Engagement-Ereignisse: 12 Monate, danach Löschung oder Anonymisierung.</li>
        <li>Kontodaten: bis zur Löschung des Kontos; Refresh-Tokens nach Ablauf (14 Tage).</li>
        <li>Passwort-Reset-Token: 60 Minuten.</li>
        <li>Artikel in der Datenbank: solange der Dienst besteht.</li>
      </ul>

      <h2>5. Hosting und Auftragsverarbeiter / Хостинг</h2>
      <ul>
        <li>
          <strong>Application-Server und Datenbank</strong> — Standort {legal.hostingCountry} (VPS/Server
          beim gewählten Anbieter in DE).
        </li>
        <li>
          <strong>OpenAI</strong> (USA) — Verarbeitung von Nachrichtentexten; Datenübermittlung mit
          Standardvertragsklauseln des Anbieters.
        </li>
        <li>
          <strong>Telegram Messenger LLP</strong> — Versand von Kurzmeldungen in einen konfigurierten Kanal.
        </li>
        <li>
          <strong>GMX / mail.gmx.net</strong> — Versand von Passwort-Reset-E-Mails.
        </li>
        <li>
          <strong>Sentry / Prometheus</strong> — derzeit nicht aktiv (kein DSN / Metrics aus).
        </li>
      </ul>

      <h2>6. Browser-Speicher (TTDSG) / localStorage</h2>
      <ul>
        <li>
          <strong>Ohne Einwilligung:</strong> Login-Tokens (<code>newsfr.auth.*</code>) bei angemeldeten
          Nutzern; lokale „nützlich“-Markierungen nur im Gerät.
        </li>
        <li>
          <strong>Nur mit Einwilligung (Banner):</strong> <code>nga_analytics_consent</code>,{" "}
          <code>nga_anonymous_user_id</code>, <code>nga_session_id</code>, Senden von Events an den
          Server.
        </li>
      </ul>
      <AnalyticsRevokeButton />

      <h2>7. Ihre Rechte / Права (Art. 15–21 DSGVO)</h2>
      <p>
        Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit (wo anwendbar),
        Widerspruch gegen Verarbeitung nach Art. 6 Abs. 1 lit. f, Widerruf der Einwilligung zur
        Analytik jederzeit (Button oben oder Banner erneut durch Löschen von{" "}
        <code>nga_analytics_consent</code> im Browser).
      </p>
      <p>
        Beschwerde bei einer Aufsichtsbehörde — für Wohnsitz in Deutschland die zuständige
        Landesdatenschutzbehörde (z. B. Berlin:{" "}
        <a href="https://www.datenschutz-berlin.de/" rel="noopener noreferrer" target="_blank">
          Berliner Beauftragte für Datenschutz
        </a>
        ).
      </p>

      <h2>8. Automatisierte Veröffentlichung</h2>
      <p>
        Artikel können nach RSS-Import und KI-Bewertung automatisch veröffentlicht oder zur Moderation
        vorgelegt werden (Schwellwert auf dem Server). Das betrifft Inhalte, nicht Profilierung von
        Lesern.
      </p>

      <h2>9. Minderjährige</h2>
      <p>Der Dienst richtet sich nicht an Personen unter 16 Jahren.</p>

      <p className="muted">
        Vollständige Vorlage im Repository: <code>docs/privacy-EU-DE.md</code>
      </p>
    </section>
  );
}
