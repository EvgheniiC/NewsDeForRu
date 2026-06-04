/** TTDSG / ePrivacy: engagement analytics only after explicit opt-in. */

import { clearAnonymousUserId } from "./anonymousUserId";

export type AnalyticsConsentValue = "granted" | "denied";

const STORAGE_KEY: string = "nga_analytics_consent";
const STORAGE_AT_KEY: string = "nga_analytics_consent_at";

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

/** ISO timestamp when user last chose granted or denied (browser only, not sent to server). */
export function getAnalyticsConsentRecordedAt(): string | null {
  try {
    return window.localStorage.getItem(STORAGE_AT_KEY);
  } catch {
    return null;
  }
}

function recordConsentChoice(value: AnalyticsConsentValue): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, value);
    window.localStorage.setItem(STORAGE_AT_KEY, new Date().toISOString());
  } catch {
    /* ignore quota / private mode */
  }
}

export function grantAnalyticsConsent(): void {
  recordConsentChoice("granted");
  notifyListeners();
}

export function denyAnalyticsConsent(): void {
  recordConsentChoice("denied");
  clearAnonymousUserId();
  notifyListeners();
}

/** Clears consent so the banner can be shown again; stops analytics immediately. */
export function revokeAnalyticsConsent(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
    window.localStorage.removeItem(STORAGE_AT_KEY);
  } catch {
    /* ignore */
  }
  clearAnonymousUserId();
  notifyListeners();
}

export function subscribeAnalyticsConsent(listener: ConsentListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
