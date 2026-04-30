/** Pure helpers for pipeline / server status UI (easy to unit test). */

import { formatDateTimeRuBerlin } from "./dateTimeBerlin";

export function formatHealthTime(iso: string | null): string {
  return formatDateTimeRuBerlin(iso);
}

/** User-visible note when backend returns ok:false without structured error body. */
export function describePipelinePartialFailure(run: { ok: boolean; error: string | null }): string | null {
  if (!run.ok && !run.error) {
    return "Пайплайн завершился с ok: false";
  }
  return null;
}
