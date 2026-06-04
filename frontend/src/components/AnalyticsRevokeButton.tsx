import { useEffect, useState } from "react";
import {
  hasAnalyticsConsent,
  revokeAnalyticsConsent,
  subscribeAnalyticsConsent,
} from "../lib/analyticsConsent";
import type { LegalLocale } from "../lib/legalLocale";

const LABELS: Record<LegalLocale, string> = {
  de: "Einwilligung zur Nutzungsanalyse widerrufen",
  ru: "Отозвать согласие на аналитику",
};

interface AnalyticsRevokeButtonProps {
  locale: LegalLocale;
}

export function AnalyticsRevokeButton({ locale }: AnalyticsRevokeButtonProps): JSX.Element | null {
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
        {LABELS[locale]}
      </button>
    </p>
  );
}
