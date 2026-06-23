import { describe, expect, it } from "vitest";

import type { ProcessedNews } from "../types/news";
import { berlinDayOffsetFromToday, groupModerationQueueByPeriod } from "./moderationQueue";

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

describe("groupModerationQueueByPeriod", () => {
  const now: Date = new Date("2026-06-23T12:00:00+02:00");

  it("places items into today, last 3 days, and week sections", () => {
    const items: ProcessedNews[] = [
      makeItem(1, "2026-06-23T08:00:00+02:00"),
      makeItem(2, "2026-06-22T08:00:00+02:00"),
      makeItem(3, "2026-06-20T08:00:00+02:00"),
      makeItem(4, "2026-06-16T08:00:00+02:00"),
      makeItem(5, "2026-06-10T08:00:00+02:00"),
    ];

    const sections = groupModerationQueueByPeriod(items, now);

    expect(sections[0]?.items.map((item: ProcessedNews) => item.id)).toEqual([1]);
    expect(sections[1]?.items.map((item: ProcessedNews) => item.id)).toEqual([2, 3]);
    expect(sections[2]?.items.map((item: ProcessedNews) => item.id)).toEqual([4]);
  });

  it("sorts items within a section by created_at descending", () => {
    const items: ProcessedNews[] = [
      makeItem(1, "2026-06-21T08:00:00+02:00"),
      makeItem(2, "2026-06-22T18:00:00+02:00"),
    ];

    const lastThreeDays = groupModerationQueueByPeriod(items, now)[1];

    expect(lastThreeDays?.items.map((item: ProcessedNews) => item.id)).toEqual([2, 1]);
  });
});

describe("berlinDayOffsetFromToday", () => {
  it("returns 0 for the same Berlin calendar day", () => {
    const now: Date = new Date("2026-06-23T23:30:00+02:00");
    expect(berlinDayOffsetFromToday("2026-06-23T01:00:00+02:00", now)).toBe(0);
  });
});
