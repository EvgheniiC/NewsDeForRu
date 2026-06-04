/** TTDSG / ePrivacy: engagement analytics only after explicit opt-in. */

import { clearAnonymousUserId } from "./anonymousUserId";

export type AnalyticsConsentValue = "granted" | "denied";

const STORAGE_KEY: string = "nga_analytics_consent";

type ConsentListener = () => void;

const listeners: Set<ConsentListener> = new Set();

function notifyListeners(): void {
  for (const listener of listeners) {
    listener();
  }
}

export function getAnalyticsConsent(): AnalyticsConsentValue | null {
  try {
    const raw: string | null = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "granted" || raw === "denied") {
      return raw;
    }
    return null;
  } catch {
    return null;
  }
}

export function hasAnalyticsConsent(): boolean {
  return getAnalyticsConsent() === "granted";
}

export function grantAnalyticsConsent(): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, "granted");
  } catch {
    /* ignore quota / private mode */
  }
  notifyListeners();
}

export function denyAnalyticsConsent(): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, "denied");
  } catch {
    /* ignore */
  }
  clearAnonymousUserId();
  notifyListeners();
}

export function revokeAnalyticsConsent(): void {
  denyAnalyticsConsent();
}

export function subscribeAnalyticsConsent(listener: ConsentListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
