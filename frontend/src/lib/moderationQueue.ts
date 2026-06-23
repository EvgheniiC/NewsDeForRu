import { APP_TIME_ZONE } from "./dateTimeBerlin";
import type { ProcessedNews } from "../types/news";

export type ModerationQueueSectionKey = "today" | "last_3_days" | "week";

export interface ModerationQueueSection {
  key: ModerationQueueSectionKey;
  label: string;
  items: ProcessedNews[];
}

interface BerlinYmd {
  year: number;
  month: number;
  day: number;
}

const SECTION_ORDER: readonly ModerationQueueSectionKey[] = ["today", "last_3_days", "week"];

const SECTION_LABELS: Record<ModerationQueueSectionKey, string> = {
  today: "Сегодня",
  last_3_days: "Последние 3 дня",
  week: "Неделя",
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

function sectionKeyForDayOffset(dayOffset: number): ModerationQueueSectionKey | null {
  if (dayOffset === 0) {
    return "today";
  }
  if (dayOffset >= 1 && dayOffset <= 3) {
    return "last_3_days";
  }
  if (dayOffset >= 4 && dayOffset <= 7) {
    return "week";
  }
  return null;
}

function compareByCreatedAtDesc(left: ProcessedNews, right: ProcessedNews): number {
  return new Date(right.created_at).getTime() - new Date(left.created_at).getTime();
}

/** Split moderation queue into non-overlapping Berlin calendar sections (max 7 days). */
export function groupModerationQueueByPeriod(
  items: ProcessedNews[],
  now: Date = new Date(),
): ModerationQueueSection[] {
  const buckets: Record<ModerationQueueSectionKey, ProcessedNews[]> = {
    today: [],
    last_3_days: [],
    week: [],
  };

  for (const item of items) {
    const sectionKey: ModerationQueueSectionKey | null = sectionKeyForDayOffset(
      berlinDayOffsetFromToday(item.created_at, now),
    );
    if (sectionKey !== null) {
      buckets[sectionKey].push(item);
    }
  }

  return SECTION_ORDER.map((key: ModerationQueueSectionKey) => ({
    key,
    label: SECTION_LABELS[key],
    items: buckets[key].toSorted(compareByCreatedAtDesc),
  }));
}
