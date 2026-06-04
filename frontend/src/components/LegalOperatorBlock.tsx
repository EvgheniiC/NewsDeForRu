import { getLegalConfig } from "../config/legal";

export function LegalOperatorBlock(): JSX.Element {
  const legal = getLegalConfig();

  if (!legal.operatorComplete) {
    return (
      <p className="legal-warning" role="status">
        Для публикации укажите в <code>frontend/.env</code>:{" "}
        <code>VITE_LEGAL_OPERATOR_NAME</code>, <code>VITE_LEGAL_OPERATOR_STREET</code>,{" "}
        <code>VITE_LEGAL_OPERATOR_POSTAL_CITY</code>, <code>VITE_LEGAL_CONTACT_EMAIL</code>.
      </p>
    );
  }

  return (
    <address className="legal-address">
      {legal.operatorName}
      <br />
      {legal.operatorStreet}
      <br />
      {legal.operatorPostalCity}
      <br />
      <a href={`mailto:${legal.contactEmail}`}>{legal.contactEmail}</a>
    </address>
  );
}
