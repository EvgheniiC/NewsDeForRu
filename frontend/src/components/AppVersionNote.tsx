import { useAppVersion } from "../hooks/useAppVersion";
import type { LegalLocale } from "../lib/legalLocale";

interface AppVersionNoteProps {
  locale: LegalLocale;
}

export function AppVersionNote({ locale }: AppVersionNoteProps): JSX.Element {
  const version: string = useAppVersion();
  const label: string = locale === "de" ? "App-Version" : "Версия приложения";

  return (
    <p className="muted">
      {label}: {version}
    </p>
  );
}
