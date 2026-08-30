import { LegalOperatorBlock } from "../../components/LegalOperatorBlock";
import { getLegalConfig } from "../../config/legal";

export function ImpressumContentDe(): JSX.Element {
  const legal = getLegalConfig();

  return (
    <>
      <h1>Impressum</h1>
      <p className="muted">
        Angaben gemäß § 5 TMG für{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>.
      </p>

      <h2>Diensteanbieter</h2>
      <LegalOperatorBlock locale="de" />
      <p>
        Einzelunternehmerin. Keine Umsatzsteuer-ID, sofern nicht umsatzsteuerpflichtig.
      </p>

      <h2>Kontakt</h2>
      {legal.contactEmail ? (
        <p>
          E-Mail: <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
        </p>
      ) : (
        <p className="legal-warning">
          Bitte <code>VITE_LEGAL_CONTACT_EMAIL</code> in frontend/.env setzen.
        </p>
      )}

      <h2>Verantwortlich für den Inhalt (§ 18 Abs. 2 MStV)</h2>
      <LegalOperatorBlock locale="de" />

      <h2>Haftungshinweis</h2>
      <p>
        Nachrichten stammen überwiegend aus öffentlichen RSS-Feeds und werden automatisiert
        aufbereitet; keine Gewähr für Vollständigkeit oder Richtigkeit. Externe Links führen zu
        Quellen Dritter.
      </p>

      <p className="muted">Serverstandort: {legal.hostingCountry}.</p>
    </>
  );
}
