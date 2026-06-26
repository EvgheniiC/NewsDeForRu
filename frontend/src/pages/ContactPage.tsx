import { Link } from "react-router-dom";
import { getLegalConfig } from "../config/legal";

export function ContactPage(): JSX.Element {
  const legal = getLegalConfig();

  return (
    <section className="legal-page">
      <h1>Контакты</h1>
      <p className="muted">
        По вопросам работы приложения, содержания ленты и запросам по персональным данным свяжитесь с
        оператором сервиса.
      </p>

      <h2>E-mail</h2>
      {legal.contactEmail ? (
        <p>
          <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
        </p>
      ) : (
        <p className="legal-warning">
          Укажите <code>VITE_LEGAL_CONTACT_EMAIL</code> в frontend/.env перед публикацией в магазине
          приложений.
        </p>
      )}

      <h2>Оператор</h2>
      {legal.operatorComplete ? (
        <p>
          {legal.operatorName}, {legal.operatorStreet}, {legal.operatorPostalCity}
        </p>
      ) : (
        <p className="legal-warning">Заполните поля VITE_LEGAL_OPERATOR_* в frontend/.env.</p>
      )}

      <p className="muted">
        Правовая информация: <Link to="/impressum">Impressum</Link> ·{" "}
        <Link to="/privacy">Конфиденциальность</Link>
      </p>
    </section>
  );
}
