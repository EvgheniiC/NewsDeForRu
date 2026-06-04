import { useEffect, useState } from "react";
import {
  hasAnalyticsConsent,
  revokeAnalyticsConsent,
  subscribeAnalyticsConsent,
} from "../lib/analyticsConsent";

export function AnalyticsRevokeButton(): JSX.Element | null {
  const [granted, setGranted] = useState<boolean>(hasAnalyticsConsent());

  useEffect(() => {
    return subscribeAnalyticsConsent(() => {
      setGranted(hasAnalyticsConsent());
    });
  }, []);

  if (!granted) {
    return null;
  }

  return (
    <p>
      <button className="legal-revoke-consent" onClick={revokeAnalyticsConsent} type="button">
        Согласие на аналитику отозвать / Einwilligung zur Nutzungsanalyse widerrufen
      </button>
    </p>
  );
}
