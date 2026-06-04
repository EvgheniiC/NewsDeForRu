/** UI language for legal pages and consent banner (not app-wide i18n). */

export type LegalLocale = "de" | "ru";

const STORAGE_KEY: string = "nga_legal_locale";

type LocaleListener = () => void;

const listeners: Set<LocaleListener> = new Set();

function notifyListeners(): void {
  for (const listener of listeners) {
    listener();
  }
}

function detectDefaultLocale(): LegalLocale {
  if (typeof navigator !== "undefined" && navigator.language.toLowerCase().startsWith("ru")) {
    return "ru";
  }
  return "de";
}

export function getLegalLocale(): LegalLocale {
  try {
    const raw: string | null = window.localStorage.getItem(STORAGE_KEY);
    if (raw === "de" || raw === "ru") {
      return raw;
    }
  } catch {
    /* ignore */
  }
  return detectDefaultLocale();
}

export function setLegalLocale(locale: LegalLocale): void {
  try {
    window.localStorage.setItem(STORAGE_KEY, locale);
  } catch {
    /* ignore */
  }
  notifyListeners();
}

export function subscribeLegalLocale(listener: LocaleListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}
