/** Opt-in for urgent-news push on native Android (stored locally; server stores FCM token). */

export type UrgentPushConsentValue = "granted" | "denied";

const STORAGE_KEY: string = "nga_urgent_push_consent";

type ConsentListener = () => void;

const listeners: Set<ConsentListener> = new Set();

function notifyListeners(): void {
  for (const listener of listeners) {
    listener();
  }
}

export function getUrgentPushConsent(): UrgentPushConsentValue | null {
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

export function hasUrgentPushConsent(): boolean {
  return getUrgentPushConsent() === "granted";
}

function recordConsent(value: UrgentPushConsentValue): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, value);
  } catch {
    /* ignore quota / private mode */
  }
}

export function grantUrgentPushConsent(): void {
  recordConsent("granted");
  notifyListeners();
}

export function denyUrgentPushConsent(): void {
  recordConsent("denied");
  notifyListeners();
}

export function clearUrgentPushConsent(): void {
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch {
    /* ignore */
  }
  notifyListeners();
}

export function subscribeUrgentPushConsent(listener: ConsentListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

const DEVICE_TOKEN_KEY: string = "nga_urgent_push_device_token";

export function getStoredPushDeviceToken(): string | null {
  try {
    const raw: string | null = window.localStorage.getItem(DEVICE_TOKEN_KEY);
    return raw && raw.length >= 20 ? raw : null;
  } catch {
    return null;
  }
}

export function setStoredPushDeviceToken(token: string): void {
  try {
    window.localStorage.setItem(DEVICE_TOKEN_KEY, token);
  } catch {
    /* ignore */
  }
}

export function clearStoredPushDeviceToken(): void {
  try {
    window.localStorage.removeItem(DEVICE_TOKEN_KEY);
  } catch {
    /* ignore */
  }
}
