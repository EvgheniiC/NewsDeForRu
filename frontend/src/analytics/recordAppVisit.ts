import { postAppVisit } from "../api/client";
import { berlinTodayYmd } from "../lib/dateTimeBerlin";
import { hasAnalyticsConsent, subscribeAnalyticsConsent } from "../lib/analyticsConsent";
import { getSessionId } from "../lib/sessionId";

const RECORDED_DAY_KEY: string = "nga_visit_recorded_on";

function recordedDay(): string | null {
  try {
    return window.sessionStorage.getItem(RECORDED_DAY_KEY);
  } catch {
    return null;
  }
}

function rememberRecordedDay(day: string): void {
  try {
    window.sessionStorage.setItem(RECORDED_DAY_KEY, day);
  } catch {
    /* sessionStorage may be unavailable */
  }
}

/** One visit per browser session and Berlin day, after analytics consent. */
export async function recordAppVisitIfNeeded(): Promise<void> {
  if (!hasAnalyticsConsent()) {
    return;
  }
  const day: string = berlinTodayYmd();
  if (recordedDay() === day) {
    return;
  }
  await postAppVisit(getSessionId());
  rememberRecordedDay(day);
}

export function startAppVisitRecording(): () => void {
  const record = (): void => {
    void recordAppVisitIfNeeded().catch((): void => {
      /* Retry on the next open or when the tab becomes visible. */
    });
  };

  record();
  const unsubscribe: () => void = subscribeAnalyticsConsent(record);
  const onVisible = (): void => {
    if (document.visibilityState === "visible") {
      record();
    }
  };
  document.addEventListener("visibilitychange", onVisible);

  return (): void => {
    unsubscribe();
    document.removeEventListener("visibilitychange", onVisible);
  };
}
