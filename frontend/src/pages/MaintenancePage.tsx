import { Link } from "react-router-dom";
import { LegalLanguageSwitch } from "../components/LegalLanguageSwitch";
import { useDocumentHead } from "../hooks/useDocumentHead";
import { useLegalLocale } from "../hooks/useLegalLocale";
import type { LegalLocale } from "../lib/legalLocale";
import { SITE_DESCRIPTION } from "../lib/seo";

interface MaintenanceCopy {
  readonly title: string;
  readonly documentTitle: string;
  readonly lead: string;
  readonly body: string;
  readonly impressum: string;
  readonly privacy: string;
  readonly contact: string;
}

const COPY: Record<LegalLocale, MaintenanceCopy> = {
  de: {
    title: "Website in Überarbeitung",
    documentTitle: "Überarbeitung — newsForGermanyRU",
    lead: "Die öffentliche Version ist vorübergehend nicht erreichbar.",
    body: "Wir arbeiten an der Seite und öffnen sie wieder, sobald alles bereit ist. Bitte schauen Sie später noch einmal vorbei.",
    impressum: "Impressum",
    privacy: "Datenschutz",
    contact: "Kontakt",
  },
  ru: {
    title: "Сайт на реконструкции",
    documentTitle: "Реконструкция — newsForGermanyRU",
    lead: "Публичная версия временно закрыта.",
    body: "Мы дорабатываем сайт и откроем его снова, когда всё будет готово. Загляните позже.",
    impressum: "Impressum",
    privacy: "Конфиденциальность",
    contact: "Контакты",
  },
};

export function MaintenancePage(): JSX.Element {
  const [locale] = useLegalLocale();
  const copy: MaintenanceCopy = COPY[locale];

  useDocumentHead({
    title: copy.documentTitle,
    description: SITE_DESCRIPTION,
    canonicalPath: "/",
    robots: "noindex, nofollow",
  });

  return (
    <section className="maintenance-page">
      <article className="maintenance-card">
        <LegalLanguageSwitch />
        <h1>{copy.title}</h1>
        <p className="maintenance-lead">{copy.lead}</p>
        <p>{copy.body}</p>
        <p className="muted maintenance-links">
          <Link to="/impressum">{copy.impressum}</Link>
          {" · "}
          <Link to="/privacy">{copy.privacy}</Link>
          {" · "}
          <Link to="/contact">{copy.contact}</Link>
        </p>
      </article>
    </section>
  );
}
