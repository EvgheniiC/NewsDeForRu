import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  denyAnalyticsConsent,
  getAnalyticsConsent,
  grantAnalyticsConsent,
  subscribeAnalyticsConsent,
} from "../lib/analyticsConsent";

export function AnalyticsConsentBanner(): JSX.Element | null {
  const [pending, setPending] = useState<boolean>(getAnalyticsConsent() === null);

  useEffect(() => {
    return subscribeAnalyticsConsent(() => {
      setPending(getAnalyticsConsent() === null);
    });
  }, []);

  if (!pending) {
    return null;
  }

  return (
    <aside aria-label="Einwilligung zur Nutzungsanalyse" className="consent-banner" role="dialog">
      <p className="consent-banner-text">
        <strong>Nutzungsanalyse (optional).</strong> Wir speichern pseudonyme Kennungen im Browser und
        senden aggregierte Ereignisse (z. B. geöffnete Artikel, „nützlich“) an unseren Server in
        Deutschland — nur mit Ihrer Einwilligung (TTDSG / DSGVO). Anmeldung und Lesen der Lenta
        funktionieren auch ohne Zustimmung zur Analyse.
      </p>
      <p className="consent-banner-text consent-banner-text-muted">
        <strong>Аналитика (по желанию).</strong> Псевдонимные ID в браузере и события на сервер в
        Германии — только после согласия. Лента и аккаунт работают без этого.
      </p>
      <div className="consent-banner-actions">
        <button className="consent-banner-accept" onClick={grantAnalyticsConsent} type="button">
          Akzeptieren / Принять
        </button>
        <button className="consent-banner-decline" onClick={denyAnalyticsConsent} type="button">
          Ablehnen / Отклонить
        </button>
        <Link className="consent-banner-link" to="/privacy">
          Datenschutz / Конфиденциальность
        </Link>
      </div>
    </aside>
  );
}
