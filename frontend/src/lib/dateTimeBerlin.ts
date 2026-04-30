/** Single display timezone for the app (operators and users in Germany). */
export const APP_TIME_ZONE: string = "Europe/Berlin";

export function formatDateTimeRuBerlin(isoOrTimestamp: string | null | undefined): string {
  if (!isoOrTimestamp) {
    return "—";
  }
  try {
    const d: Date = new Date(isoOrTimestamp);
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "short",
      timeStyle: "medium",
      timeZone: APP_TIME_ZONE
    }).format(d);
  } catch {
    return isoOrTimestamp;
  }
}
