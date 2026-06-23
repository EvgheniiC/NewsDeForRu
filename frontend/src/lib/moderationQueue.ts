import { APP_TIME_ZONE } from "./dateTimeBerlin";
import type { ProcessedNews } from "../types/news";

export type ModerationPeriodKey = "today" | "last_3_days" | "week";

export interface ModerationPeriodOption {
  key: ModerationPeriodKey;
  label: string;
}

export const MODERATION_PERIOD_OPTIONS: readonly ModerationPeriodOption[] = [
  { key: "today", label: "Сегодня" },
  { key: "last_3_days", label: "3 дня" },
  { key: "week", label: "Неделя" },
];

interface BerlinYmd {
  year: number;
  month: number;
  day: number;
}

/** Inclusive max Berlin day offset for each rolling period (0 = today). */
const PERIOD_MAX_DAY_OFFSET: Record<ModerationPeriodKey, number> = {
  today: 0,
  last_3_days: 2,
  week: 7,
};

function getBerlinYmd(date: Date): BerlinYmd {
  const parts: Intl.DateTimeFormatPart[] = new Intl.DateTimeFormat("en-US", {
    timeZone: APP_TIME_ZONE,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(date);

  const yearPart: Intl.DateTimeFormatPart | undefined = parts.find(
    (part: Intl.DateTimeFormatPart) => part.type === "year",
  );
  const monthPart: Intl.DateTimeFormatPart | undefined = parts.find(
    (part: Intl.DateTimeFormatPart) => part.type === "month",
  );
  const dayPart: Intl.DateTimeFormatPart | undefined = parts.find(
    (part: Intl.DateTimeFormatPart) => part.type === "day",
  );

  if (yearPart === undefined || monthPart === undefined || dayPart === undefined) {
    throw new Error("Failed to parse Berlin calendar date.");
  }

  return {
    year: Number(yearPart.value),
    month: Number(monthPart.value),
    day: Number(dayPart.value),
  };
}

function berlinDayNumber(ymd: BerlinYmd): number {
  return Math.floor(Date.UTC(ymd.year, ymd.month - 1, ymd.day) / 86_400_000);
}

/** Calendar day offset in Europe/Berlin: 0 = today, 1 = yesterday, etc. */
export function berlinDayOffsetFromToday(isoOrTimestamp: string, now: Date = new Date()): number {
  const createdYmd: BerlinYmd = getBerlinYmd(new Date(isoOrTimestamp));
  const nowYmd: BerlinYmd = getBerlinYmd(now);
  return berlinDayNumber(nowYmd) - berlinDayNumber(createdYmd);
}

function compareByCreatedAtDesc(left: ProcessedNews, right: ProcessedNews): number {
  return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
}

function isInModerationPeriod(
  createdAtIso: string,
  period: ModerationPeriodKey,
  now: Date = new Date(),
): boolean {
  const dayOffset: number = berlinDayOffsetFromToday(createdAtIso, now);
  return dayOffset >= 0 && dayOffset <= PERIOD_MAX_DAY_OFFSET[period];
}

/** Filter moderation queue by rolling Berlin calendar period; newest first. */
export function filterModerationQueueByPeriod(
  items: ProcessedNews[],
  period: ModerationPeriodKey,
  now: Date = new Date(),
): ProcessedNews[] {
  return items
    .filter((item: ProcessedNews) => isInModerationPeriod(item.created_at, period, now))
    .toSorted(compareByCreatedAtDesc);
}

export function countModerationQueueByPeriod(
  items: ProcessedNews[],
  now: Date = new Date(),
): Record<ModerationPeriodKey, number> {
  return {
    today: filterModerationQueueByPeriod(items, "today", now).length,
    last_3_days: filterModerationQueueByPeriod(items, "last_3_days", now).length,
    week: filterModerationQueueByPeriod(items, "week", now).length,
  };
}
