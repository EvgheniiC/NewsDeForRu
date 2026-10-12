import { Capacitor } from "@capacitor/core";

import { postAppInstall } from "../api/client";
import { hasAnalyticsConsent, subscribeAnalyticsConsent } from "../lib/analyticsConsent";
import { getInstallId } from "../lib/installId";

const REPORTED_KEY: string = "nga_install_reported";

function isAndroidApp(): boolean {
  return Capacitor.isNativePlatform() && Capacitor.getPlatform() === "android";
}

function installAlreadyReported(): boolean {
  try {
    return window.localStorage.getItem(REPORTED_KEY) === "1";
  } catch {
    return false;
  }
}

function rememberInstallReported(): void {
  try {
    window.localStorage.setItem(REPORTED_KEY, "1");
  } catch {
    /* localStorage may be unavailable */
  }
}

/** One Android download per install, after analytics consent. Web visits are ignored. */
export async function recordAppInstallIfNeeded(): Promise<void> {
  if (!isAndroidApp() || !hasAnalyticsConsent() || installAlreadyReported()) {
    return;
  }
  await postAppInstall(getInstallId());
  rememberInstallReported();
}

export function startAppInstallRecording(): () => void {
  const record = (): void => {
    void recordAppInstallIfNeeded().catch((): void => {
      /* Retry on the next open or when the app becomes visible. */
    });
  };

  record();
  const unsubscribe: () => void = subscribeAnalyticsConsent(record);
  const onVisible = (): void => {
    if (document.visibilityState === "visible") {
      record();
    }
  };
  document.addEventListener("visibilitychange", onVisible);

  return (): void => {
    unsubscribe();
    document.removeEventListener("visibilitychange", onVisible);
  };
}
