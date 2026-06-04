import { getLegalConfig } from "../config/legal";
import type { LegalLocale } from "../lib/legalLocale";

interface LegalOperatorBlockProps {
  locale: LegalLocale;
}

export function LegalOperatorBlock({ locale }: LegalOperatorBlockProps): JSX.Element {
  const legal = getLegalConfig();

  if (!legal.operatorComplete) {
    const message: string =
      locale === "de"
        ? "Bitte in frontend/.env setzen: VITE_LEGAL_OPERATOR_NAME, VITE_LEGAL_OPERATOR_STREET, VITE_LEGAL_OPERATOR_POSTAL_CITY, VITE_LEGAL_CONTACT_EMAIL."
        : "Для публикации укажите в frontend/.env: VITE_LEGAL_OPERATOR_NAME, VITE_LEGAL_OPERATOR_STREET, VITE_LEGAL_OPERATOR_POSTAL_CITY, VITE_LEGAL_CONTACT_EMAIL.";
    return (
      <p className="legal-warning" role="status">
        {message}
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
