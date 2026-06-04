/** Operator and site metadata for Impressum / Datenschutz (set via frontend/.env). */
export interface LegalConfig {
  readonly operatorName: string;
  readonly operatorStreet: string;
  readonly operatorPostalCity: string;
  readonly contactEmail: string;
  readonly publicAppBaseUrl: string;
  readonly hostingCountry: string;
  readonly operatorComplete: boolean;
}

function envString(key: keyof ImportMetaEnv): string {
  const raw: string | undefined = import.meta.env[key]?.trim();
  return raw ?? "";
}

export function getLegalConfig(): LegalConfig {
  const operatorName: string = envString("VITE_LEGAL_OPERATOR_NAME");
  const operatorStreet: string = envString("VITE_LEGAL_OPERATOR_STREET");
  const operatorPostalCity: string = envString("VITE_LEGAL_OPERATOR_POSTAL_CITY");
  const contactEmail: string = envString("VITE_LEGAL_CONTACT_EMAIL");
  const publicAppBaseUrl: string =
    envString("VITE_PUBLIC_APP_BASE_URL") || "https://simplenewsapp.de";

  return {
    operatorName,
    operatorStreet,
    operatorPostalCity,
    contactEmail,
    publicAppBaseUrl,
    hostingCountry: "Deutschland",
    operatorComplete:
      operatorName.length > 0 &&
      operatorStreet.length > 0 &&
      operatorPostalCity.length > 0 &&
      contactEmail.length > 0,
  };
}
