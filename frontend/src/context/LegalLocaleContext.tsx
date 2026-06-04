import React, { createContext, useContext, useEffect, useMemo, useState } from "react";

import {
  getLegalLocale,
  setLegalLocale,
  subscribeLegalLocale,
  type LegalLocale,
} from "../lib/legalLocale";

interface LegalLocaleContextValue {
  readonly locale: LegalLocale;
  readonly setLocale: (locale: LegalLocale) => void;
}

const LegalLocaleContext = createContext<LegalLocaleContextValue | null>(null);

export function LegalLocaleProvider({ children }: { children: React.ReactNode }): JSX.Element {
  const [locale, setLocaleState] = useState<LegalLocale>(getLegalLocale);

  useEffect(() => {
    return subscribeLegalLocale(() => {
      setLocaleState(getLegalLocale());
    });
  }, []);

  const setLocale = (next: LegalLocale): void => {
    setLegalLocale(next);
    setLocaleState(next);
  };

  const value = useMemo(
    (): LegalLocaleContextValue => ({ locale, setLocale }),
    [locale]
  );

  return <LegalLocaleContext.Provider value={value}>{children}</LegalLocaleContext.Provider>;
}

export function useLegalLocale(): [LegalLocale, (locale: LegalLocale) => void] {
  const ctx: LegalLocaleContextValue | null = useContext(LegalLocaleContext);
  if (ctx === null) {
    throw new Error("useLegalLocale requires LegalLocaleProvider");
  }
  return [ctx.locale, ctx.setLocale];
}
