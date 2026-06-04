import { LegalOperatorBlock } from "../components/LegalOperatorBlock";
import { getLegalConfig } from "../config/legal";

export function ImpressumPage(): JSX.Element {
  const legal = getLegalConfig();

  return (
    <section className="legal-page">
      <h1>Impressum</h1>
      <p className="muted">
        Angaben gemäß § 5 TMG (Telemediengesetz) für{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>.
      </p>

      <h2>Diensteanbieter</h2>
      <LegalOperatorBlock />
      <p>
        Natürliche Person (privater Betreiber), keine Umsatzsteuer-ID, sofern nicht
        umsatzsteuerpflichtig.
      </p>

      <h2>Kontakt</h2>
      {legal.contactEmail ? (
        <p>
          E-Mail:{" "}
          <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
        </p>
      ) : (
        <p className="legal-warning">E-Mail: siehe <code>VITE_LEGAL_CONTACT_EMAIL</code> in .env</p>
      )}

      <h2>Verantwortlich für den Inhalt (§ 18 Abs. 2 MStV)</h2>
      <LegalOperatorBlock />

      <h2>Haftungshinweis</h2>
      <p>
        Die Nachrichten stammen überwiegend aus öffentlichen RSS-Feeds und werden automatisiert
        aufbereitet; keine Gewähr für Vollständigkeit oder Richtigkeit. Externe Links führen zu
        Quellen Dritter.
      </p>

      <h2>Импрессум (кратко)</h2>
      <p>
        Сведения об операторе по § 5 TMG для сайта{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>. Оператор — физическое лицо в
        Германии; хостинг сервера — в Германии. Контакт — e-mail выше.
      </p>
    </section>
  );
}
