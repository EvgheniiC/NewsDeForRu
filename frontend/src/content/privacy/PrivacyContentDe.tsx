import { AnalyticsRevokeButton } from "../../components/AnalyticsRevokeButton";
import { LegalOperatorBlock } from "../../components/LegalOperatorBlock";
import { getLegalConfig } from "../../config/legal";

export function PrivacyContentDe(): JSX.Element {
  const legal = getLegalConfig();

  return (
    <>
      <h1>Datenschutzerklärung</h1>
      <p className="muted">
        Stand: Juni 2026 · DSGVO, TTDSG · Dienst:{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>
      </p>
      <p className="legal-disclaimer">
        Technischer Entwurf für einen privaten Betreiber in Deutschland. Keine Rechtsberatung.
      </p>

      <h2>1. Verantwortlicher</h2>
      <LegalOperatorBlock detail="compact" locale="de" />
      <p>Datenschutzanfragen richten Sie an die oben genannte E-Mail-Adresse.</p>

      <h2>2. Überblick</h2>
      <ul>
        <li>Lesen der Nachrichten ohne Registrierung; technische Logs auf Servern in {legal.hostingCountry}.</li>
        <li>
          Optionales Konto: E-Mail, Passwort-Hash, JWT in localStorage (<code>newsfr.auth.*</code>).
        </li>
        <li>
          Nutzungsanalyse nur nach Einwilligung im Banner (pseudonyme IDs,{" "}
          <code>/engagement/events</code>).
        </li>
        <li>
          Pipeline: RSS und Datenbank in DE; Textverarbeitung über OpenAI (USA); optional Telegram.
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
              <td>Server-Logs (Zeit, Pfad, Status; keine Secrets)</td>
              <td>Betrieb, Sicherheit</td>
              <td>Art. 6 Abs. 1 lit. f</td>
            </tr>
            <tr>
              <td>RSS, Artikel, Embeddings (DB in DE)</td>
              <td>News-Pipeline</td>
              <td>Art. 6 Abs. 1 lit. f</td>
            </tr>
            <tr>
              <td>OpenAI API (gpt-4o-mini)</td>
              <td>Zusammenfassung, Übersetzung</td>
              <td>Art. 6 Abs. 1 lit. f; USA — SCC</td>
            </tr>
            <tr>
              <td>Telegram Bot API</td>
              <td>Kanal-Benachrichtigungen</td>
              <td>Art. 6 Abs. 1 lit. f</td>
            </tr>
            <tr>
              <td>Konto: E-Mail, Hash, Refresh-Token</td>
              <td>Login, Passwort-Reset</td>
              <td>Art. 6 Abs. 1 lit. b</td>
            </tr>
            <tr>
              <td>GMX SMTP (mail.gmx.net)</td>
              <td>Reset-E-Mail</td>
              <td>Art. 6 Abs. 1 lit. b</td>
            </tr>
            <tr>
              <td>
                <code>nga_anonymous_user_id</code>, <code>nga_session_id</code>, Events
              </td>
              <td>Nutzungsstatistik</td>
              <td>Art. 6 Abs. 1 lit. a (Einwilligung)</td>
            </tr>
            <tr>
              <td>JWT, lokal „nützlich“</td>
              <td>Sitzung / Anzeige</td>
              <td>lit. b / f bzw. Einwilligung für Server-Sync</td>
            </tr>
          </tbody>
        </table>
      </div>

      <h2>4. Einwilligung Banner — was passiert?</h2>
      <ul>
        <li>
          <strong>Keine Speicherung Ihrer Entscheidung auf unserem Server.</strong> Wir führen kein
          Register „wer hat zugestimmt“. Nur Ihr Browser speichert{" "}
          <code>nga_analytics_consent</code> (<code>granted</code> oder <code>denied</code>) und optional{" "}
          <code>nga_analytics_consent_at</code> (Zeitpunkt der Wahl).
        </li>
        <li>
          <strong>Akzeptieren:</strong> pseudonyme IDs dürfen gesetzt werden; aggregierte Events (z. B.
          Artikel geöffnet, „nützlich“) werden an den Server in Deutschland gesendet.
        </li>
        <li>
          <strong>Ablehnen:</strong> App und Konto funktionieren normal; <strong>keine</strong>{" "}
          Nutzungsanalyse, <strong>keine</strong> Engagement-Requests, keine dauerhafte anonyme ID.
        </li>
        <li>
          <strong>Widerruf:</strong> Button unten — Analyse stoppt, Banner erscheint erneut zur neuen
          Wahl; alternativ Einträge im Browser löschen.
        </li>
      </ul>
      <AnalyticsRevokeButton locale="de" />

      <h2>5. Speicherdauer</h2>
      <ul>
        <li>Server-Logs: bis ca. 90 Tage.</li>
        <li>Engagement-Events: 12 Monate.</li>
        <li>Konto: bis Löschung; Refresh-Token max. 14 Tage.</li>
        <li>Passwort-Reset-Token: 60 Minuten.</li>
      </ul>

      <h2>6. Auftragsverarbeiter</h2>
      <ul>
        <li>Hosting / DB — {legal.hostingCountry}.</li>
        <li>OpenAI (USA), Telegram, GMX — siehe Tabelle.</li>
        <li>Sentry / Prometheus — derzeit deaktiviert.</li>
      </ul>

      <h2>7. Ihre Rechte</h2>
      <p>
        Auskunft, Berichtigung, Löschung, Einschränkung, Widerspruch, Widerruf der Einwilligung.
        Beschwerde bei der zuständigen Landesbehörde (z. B. Niedersachsen:{" "}
        <a
          href="https://lfd.niedersachsen.de/startseite/themen/datenschutz/"
          rel="noopener noreferrer"
          target="_blank"
        >
          LfD Niedersachsen
        </a>
        ).
      </p>

      <h2>8. Automatisierte Veröffentlichung</h2>
      <p>KI-gestützte Aufbereitung von RSS-Inhalten; keine Profilierung der Leser.</p>

      <h2>9. Minderjährige</h2>
      <p>Nicht für Personen unter 16 Jahren.</p>
    </>
  );
}
