import { describe, expect, test } from "vitest";
import { activeFeedMaxAgeDays, filterActiveFeedItems, isAllReadInFetchedBatch } from "./feedVisibility";
import { markNewsAsRead, READ_RETENTION_MS } from "./readStateStorage";
import type { NewsFeedItem } from "../types/news";

function sampleItem(overrides: Partial<NewsFeedItem> = {}): NewsFeedItem {
  return {
    id: 1,
    title: "Test",
    subtitle: "Sub",
    read_time_minutes: 2,
    topic: "life",
    is_urgent: false,
    is_positive: false,
    published_at: new Date().toISOString(),
    source_name: "Test",
    created_at: new Date().toISOString(),
    ...overrides
  };
}

describe("feedVisibility", () => {
  test("activeFeedMaxAgeDays varies by category", () => {
    expect(activeFeedMaxAgeDays("top_today")).toBe(1);
    expect(activeFeedMaxAgeDays("urgent")).toBe(2);
    expect(activeFeedMaxAgeDays("life")).toBe(3);
  });

  test("filterActiveFeedItems hides read news", () => {
    localStorage.clear();
    markNewsAsRead(42);
    const items: NewsFeedItem[] = [sampleItem({ id: 42 }), sampleItem({ id: 43 })];
    const filtered = filterActiveFeedItems(items, "life");
    expect(filtered.map((item: NewsFeedItem) => item.id)).toEqual([43]);
  });

  test("isAllReadInFetchedBatch detects fully read batch", () => {
    localStorage.clear();
    markNewsAsRead(1);
    markNewsAsRead(2);
    expect(isAllReadInFetchedBatch([sampleItem({ id: 1 }), sampleItem({ id: 2 })])).toBe(true);
    expect(isAllReadInFetchedBatch([sampleItem({ id: 1 }), sampleItem({ id: 3 })])).toBe(false);
  });
});

describe("readStateStorage retention", () => {
  test("read entries expire after retention window", () => {
    localStorage.clear();
    const oldId: number = 99;
    localStorage.setItem(
      "nga_read_state_v1",
      JSON.stringify({ [String(oldId)]: { readAt: Date.now() - READ_RETENTION_MS - 1000 } })
    );
    const items: NewsFeedItem[] = [sampleItem({ id: oldId })];
    expect(filterActiveFeedItems(items, "life")).toEqual(items);
  });
});
