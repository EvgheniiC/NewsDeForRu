/** Pure helpers for pipeline / server status UI (easy to unit test). */

export function formatHealthTime(iso: string | null): string {
  if (!iso) {
    return "—";
  }
  try {
    const d: Date = new Date(iso);
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "short",
      timeStyle: "medium"
    }).format(d);
  } catch {
    return iso;
  }
}

/** User-visible note when backend returns ok:false without structured error body. */
export function describePipelinePartialFailure(run: { ok: boolean; error: string | null }): string | null {
  if (!run.ok && !run.error) {
    return "Пайплайн завершился с ok: false";
  }
  return null;
}
