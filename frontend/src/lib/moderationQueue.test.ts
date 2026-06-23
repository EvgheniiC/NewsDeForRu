import { describe, expect, it } from "vitest";

import type { ProcessedNews } from "../types/news";
import {
  berlinDayOffsetFromToday,
  countModerationQueueByPeriod,
  filterModerationQueueByPeriod,
} from "./moderationQueue";

function makeItem(id: number, createdAt: string): ProcessedNews {
  return {
    id,
    title: `Title ${id}`,
    one_sentence_summary: "Summary",
    plain_language: "Plain",
    impact_presentation: "multi",
    impact_owner: "",
    impact_tenant: "",
    impact_buyer: "",
    action_items: "",
    spoiler: "",
    source_url: `https://example.com/${id}`,
    image_url: null,
    topic: "life",
    is_urgent: false,
    is_positive: false,
    created_at: createdAt,
  };
}

describe("filterModerationQueueByPeriod", () => {
  const now: Date = new Date("2026-06-23T12:00:00+02:00");
  const items: ProcessedNews[] = [
    makeItem(1, "2026-06-23T08:00:00+02:00"),
    makeItem(2, "2026-06-22T08:00:00+02:00"),
    makeItem(3, "2026-06-21T08:00:00+02:00"),
    makeItem(4, "2026-06-16T08:00:00+02:00"),
    makeItem(5, "2026-06-10T08:00:00+02:00"),
  ];

  it("returns only today items for today period", () => {
    expect(filterModerationQueueByPeriod(items, "today", now).map((item) => item.id)).toEqual([1]);
  });

  it("returns rolling 3-day window for last_3_days period", () => {
    expect(filterModerationQueueByPeriod(items, "last_3_days", now).map((item) => item.id)).toEqual([
      1, 2, 3,
    ]);
  });

  it("returns rolling week window for week period", () => {
    expect(filterModerationQueueByPeriod(items, "week", now).map((item) => item.id)).toEqual([
      1, 2, 3, 4,
    ]);
  });

  it("sorts items by created_at descending", () => {
    const lastThreeDays = filterModerationQueueByPeriod(
      [makeItem(1, "2026-06-21T08:00:00+02:00"), makeItem(2, "2026-06-22T18:00:00+02:00")],
      "last_3_days",
      now,
    );

    expect(lastThreeDays.map((item) => item.id)).toEqual([2, 1]);
  });
});

describe("countModerationQueueByPeriod", () => {
  it("counts items per rolling period", () => {
    const now: Date = new Date("2026-06-23T12:00:00+02:00");
    const items: ProcessedNews[] = [
      makeItem(1, "2026-06-23T08:00:00+02:00"),
      makeItem(2, "2026-06-22T08:00:00+02:00"),
      makeItem(3, "2026-06-16T08:00:00+02:00"),
    ];

    expect(countModerationQueueByPeriod(items, now)).toEqual({
      today: 1,
      last_3_days: 2,
      week: 3,
    });
  });
});

describe("berlinDayOffsetFromToday", () => {
  it("returns 0 for the same Berlin calendar day", () => {
    const now: Date = new Date("2026-06-23T23:30:00+02:00");
    expect(berlinDayOffsetFromToday("2026-06-23T01:00:00+02:00", now)).toBe(0);
  });
});
