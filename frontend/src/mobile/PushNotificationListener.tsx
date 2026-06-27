import { Capacitor } from "@capacitor/core";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

import { hasUrgentPushConsent } from "../lib/urgentPushConsent";
import { attachPushOpenHandler, startPushRegistration } from "./urgentPush";

/** Opens /news/:id when the user taps an urgent push notification (Android). */
export function PushNotificationListener(): null {
  const navigate = useNavigate();

  useEffect((): (() => void) | void => {
    if (!Capacitor.isNativePlatform() || Capacitor.getPlatform() !== "android") {
      return;
    }

    let removeOpenHandler: (() => Promise<void>) | undefined;
    let cancelled: boolean = false;

    void (async (): Promise<void> => {
      removeOpenHandler = await attachPushOpenHandler((path: string): void => {
        navigate(path, { replace: false });
      });
      if (cancelled) {
        await removeOpenHandler();
        return;
      }
      if (hasUrgentPushConsent()) {
        await startPushRegistration();
      }
    })();

    return (): void => {
      cancelled = true;
      void removeOpenHandler?.();
    };
  }, [navigate]);

  return null;
}
