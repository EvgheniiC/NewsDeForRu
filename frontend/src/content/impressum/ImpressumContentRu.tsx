import { LegalOperatorBlock } from "../../components/LegalOperatorBlock";
import { getLegalConfig } from "../../config/legal";

export function ImpressumContentRu(): JSX.Element {
  const legal = getLegalConfig();

  return (
    <>
      <h1>Импрессум (правовая информация)</h1>
      <p className="muted">
        Сведения по § 5 TMG (Германия) для{" "}
        <a href={legal.publicAppBaseUrl}>{legal.publicAppBaseUrl}</a>.
      </p>

      <h2>Оператор сервиса</h2>
      <LegalOperatorBlock locale="ru" />
      <p>
        Физическое лицо (частный оператор). USt-IdNr. не указана, если нет обязанности по НДС.
      </p>

      <h2>Контакт</h2>
      {legal.contactEmail ? (
        <p>
          E-mail: <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
        </p>
      ) : (
        <p className="legal-warning">
          Укажите <code>VITE_LEGAL_CONTACT_EMAIL</code> в frontend/.env.
        </p>
      )}

      <h2>Ответственный за контент (§ 18 Abs. 2 MStV)</h2>
      <LegalOperatorBlock locale="ru" />

      <h2>Отказ от ответственности</h2>
      <p>
        Материалы в основном из публичных RSS-лент с автоматической обработкой; полнота и точность не
        гарантируются. Внешние ссылки ведут на сайты третьих лиц.
      </p>

      <p className="muted">Размещение сервера: {legal.hostingCountry}.</p>
    </>
  );
}
