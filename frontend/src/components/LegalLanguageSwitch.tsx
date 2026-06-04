import { useLegalLocale } from "../hooks/useLegalLocale";
import type { LegalLocale } from "../lib/legalLocale";

export function LegalLanguageSwitch(): JSX.Element {
  const [locale, setLocale] = useLegalLocale();

  return (
    <div aria-label="Sprache / язык" className="legal-lang-switch" role="group">
      <button
        aria-pressed={locale === "de"}
        className={locale === "de" ? "legal-lang-active" : undefined}
        onClick={() => setLocale("de")}
        type="button"
      >
        Deutsch
      </button>
      <button
        aria-pressed={locale === "ru"}
        className={locale === "ru" ? "legal-lang-active" : undefined}
        onClick={() => setLocale("ru")}
        type="button"
      >
        Русский
      </button>
    </div>
  );
}
