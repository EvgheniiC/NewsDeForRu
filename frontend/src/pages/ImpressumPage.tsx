import { LegalLanguageSwitch } from "../components/LegalLanguageSwitch";
import { ImpressumContentDe } from "../content/impressum/ImpressumContentDe";
import { ImpressumContentRu } from "../content/impressum/ImpressumContentRu";
import { useLegalLocale } from "../hooks/useLegalLocale";

export function ImpressumPage(): JSX.Element {
  const [locale] = useLegalLocale();

  return (
    <section className="legal-page">
      <LegalLanguageSwitch />
      {locale === "de" ? <ImpressumContentDe /> : <ImpressumContentRu />}
    </section>
  );
}
