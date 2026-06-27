import { Capacitor } from "@capacitor/core";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  getUrgentPushConsent,
  hasUrgentPushConsent,
  subscribeUrgentPushConsent,
} from "../lib/urgentPushConsent";
import { disableUrgentPushNotifications, enableUrgentPushNotifications } from "../mobile/urgentPush";

export function UrgentPushToggle(): JSX.Element | null {
  const [enabled, setEnabled] = useState<boolean>(hasUrgentPushConsent());
  const [busy, setBusy] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    return subscribeUrgentPushConsent(() => {
      setEnabled(hasUrgentPushConsent());
    });
  }, []);

  if (!Capacitor.isNativePlatform() || Capacitor.getPlatform() !== "android") {
    return null;
  }

  const onToggle = (): void => {
    void (async (): Promise<void> => {
      setBusy(true);
      setMessage(null);
      try {
        if (enabled) {
          await disableUrgentPushNotifications();
          setEnabled(false);
        } else {
          const result = await enableUrgentPushNotifications();
          if (!result.ok) {
            setMessage(result.message);
            setEnabled(getUrgentPushConsent() === "granted");
          } else {
            setEnabled(true);
          }
        }
      } catch (cause: unknown) {
        const text: string = cause instanceof Error ? cause.message : "Не удалось изменить настройку.";
        setMessage(text);
      } finally {
        setBusy(false);
      }
    })();
  };

  return (
    <div className="urgent-push-toggle">
      <label className="urgent-push-toggle-row">
        <input
          checked={enabled}
          disabled={busy}
          onChange={onToggle}
          type="checkbox"
        />
        <span>⚡ Срочные push</span>
      </label>
      <p className="urgent-push-toggle-hint">
        Только важные срочные новости. Можно отключить в любой момент.{" "}
        <Link to="/privacy">Подробнее</Link>
      </p>
      {message ? <p className="urgent-push-toggle-error">{message}</p> : null}
    </div>
  );
}
