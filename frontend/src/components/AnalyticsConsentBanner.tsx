import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useLegalLocale } from "../hooks/useLegalLocale";
import {
  denyAnalyticsConsent,
  getAnalyticsConsent,
  grantAnalyticsConsent,
  subscribeAnalyticsConsent,
} from "../lib/analyticsConsent";
import { LegalLanguageSwitch } from "./LegalLanguageSwitch";

const COPY = {
  de: {
    title: "Nutzungsanalyse (optional)",
    body:
      "Wir speichern pseudonyme Kennungen nur in Ihrem Browser und senden aggregierte Ereignisse (z. B. geöffnete Artikel) an unseren Server in Deutschland — nur wenn Sie zustimmen. Ihre Wahl wird nicht auf dem Server protokolliert. Lesen und Konto funktionieren auch ohne Zustimmung.",
    accept: "Akzeptieren",
    decline: "Ablehnen",
    privacy: "Datenschutz",
  },
  ru: {
    title: "Аналитика использования (по желанию)",
    body:
      "Псевдонимные ID хранятся только в вашем браузере; события (например, открытие статей) уходят на сервер в Германии — только после согласия. На сервере мы не ведём список «кто согласился». Лента и аккаунт работают без согласия.",
    accept: "Принять",
    decline: "Отклонить",
    privacy: "Конфиденциальность",
  },
} as const;

export function AnalyticsConsentBanner(): JSX.Element | null {
  const [pending, setPending] = useState<boolean>(getAnalyticsConsent() === null);
  const [locale] = useLegalLocale();
  const text = COPY[locale];

  useEffect(() => {
    return subscribeAnalyticsConsent(() => {
      setPending(getAnalyticsConsent() === null);
    });
  }, []);

  if (!pending) {
    return null;
  }

  return (
    <aside
      aria-label={locale === "de" ? "Einwilligung zur Nutzungsanalyse" : "Согласие на аналитику"}
      className="consent-banner"
      role="dialog"
    >
      <div className="consent-banner-top">
        <LegalLanguageSwitch />
      </div>
      <p className="consent-banner-text">
        <strong>{text.title}.</strong> {text.body}
      </p>
      <div className="consent-banner-actions">
        <button className="consent-banner-accept" onClick={grantAnalyticsConsent} type="button">
          {text.accept}
        </button>
        <button className="consent-banner-decline" onClick={denyAnalyticsConsent} type="button">
          {text.decline}
        </button>
        <Link className="consent-banner-link" to="/privacy">
          {text.privacy}
        </Link>
      </div>
    </aside>
  );
}
