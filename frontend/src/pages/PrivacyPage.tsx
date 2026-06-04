import { LegalLanguageSwitch } from "../components/LegalLanguageSwitch";
import { PrivacyContentDe } from "../content/privacy/PrivacyContentDe";
import { PrivacyContentRu } from "../content/privacy/PrivacyContentRu";
import { useLegalLocale } from "../hooks/useLegalLocale";

export function PrivacyPage(): JSX.Element {
  const [locale] = useLegalLocale();

  return (
    <section className="legal-page">
      <LegalLanguageSwitch />
      {locale === "de" ? <PrivacyContentDe /> : <PrivacyContentRu />}
    </section>
  );
}
