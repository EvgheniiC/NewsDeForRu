import { Capacitor } from "@capacitor/core";
import { PushNotifications } from "@capacitor/push-notifications";
import type { ActionPerformed, RegistrationError, Token } from "@capacitor/push-notifications";

import { subscribePush, unsubscribePush } from "../api/client";
import {
  clearStoredPushDeviceToken,
  denyUrgentPushConsent,
  getStoredPushDeviceToken,
  grantUrgentPushConsent,
  setStoredPushDeviceToken,
} from "../lib/urgentPushConsent";

let registrationStarted: boolean = false;

async function registerTokenOnServer(token: string): Promise<void> {
  await subscribePush(token);
  setStoredPushDeviceToken(token);
  grantUrgentPushConsent();
}

export async function enableUrgentPushNotifications(): Promise<{ ok: true } | { ok: false; message: string }> {
  if (!Capacitor.isNativePlatform()) {
    return { ok: false, message: "Push доступны только в мобильном приложении." };
  }
  if (Capacitor.getPlatform() !== "android") {
    return { ok: false, message: "Срочные push пока поддерживаются только на Android." };
  }

  const permission = await PushNotifications.requestPermissions();
  if (permission.receive !== "granted") {
    denyUrgentPushConsent();
    return { ok: false, message: "Разрешение на уведомления не выдано." };
  }

  await startPushRegistration();
  return { ok: true };
}

export async function disableUrgentPushNotifications(): Promise<void> {
  const token: string | null = getStoredPushDeviceToken();
  if (token !== null) {
    try {
      await unsubscribePush(token);
    } catch {
      /* server may be unreachable; still clear local opt-in */
    }
  }
  clearStoredPushDeviceToken();
  denyUrgentPushConsent();
}

export async function startPushRegistration(): Promise<void> {
  if (!Capacitor.isNativePlatform() || registrationStarted) {
    return;
  }
  registrationStarted = true;

  await PushNotifications.addListener(
    "registration",
    (event: Token): void => {
      void registerTokenOnServer(event.value);
    },
  );

  await PushNotifications.addListener(
    "registrationError",
    (error: RegistrationError): void => {
      registrationStarted = false;
      denyUrgentPushConsent();
      console.error("Push registration failed", error.error);
    },
  );

  await PushNotifications.register();
}

export async function attachPushOpenHandler(
  onOpen: (path: string) => void,
): Promise<() => Promise<void>> {
  const handle = await PushNotifications.addListener(
    "pushNotificationActionPerformed",
    (event: ActionPerformed): void => {
      const data: Record<string, unknown> = event.notification.data ?? {};
      const pathRaw: unknown = data.path;
      const newsIdRaw: unknown = data.news_id;
      if (typeof pathRaw === "string" && pathRaw.startsWith("/")) {
        onOpen(pathRaw);
        return;
      }
      if (typeof newsIdRaw === "string" && newsIdRaw.length > 0) {
        onOpen(`/news/${newsIdRaw}`);
      }
    },
  );
  return async (): Promise<void> => {
    await handle.remove();
  };
}
