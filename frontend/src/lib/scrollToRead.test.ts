import { afterEach, describe, expect, test, vi } from "vitest";
import { markNewsAsRead, READ_STATE_STORAGE_KEY } from "./readStateStorage";
import {
  flushPendingScrollRead,
  listPendingScrollReadIds,
  PENDING_SCROLL_READ_STORAGE_KEY,
  queueScrollPastNews
} from "./scrollToRead";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: (): boolean => false
  }
}));

describe("scrollToRead", () => {
  afterEach(() => {
    window.sessionStorage.clear();
    window.localStorage.clear();
  });

  test("queueScrollPastNews deduplicates pending ids", () => {
    queueScrollPastNews(10);
    queueScrollPastNews(10);
    queueScrollPastNews(11);
    expect(listPendingScrollReadIds()).toEqual([10, 11]);
  });

  test("queueScrollPastNews skips already read news", () => {
    markNewsAsRead(5);
    queueScrollPastNews(5);
    queueScrollPastNews(6);
    expect(listPendingScrollReadIds()).toEqual([6]);
  });

  test("flushPendingScrollRead marks pending news and clears session buffer", () => {
    queueScrollPastNews(1);
    queueScrollPastNews(2);
    flushPendingScrollRead();
    expect(listPendingScrollReadIds()).toEqual([]);
    const raw: string | null = window.localStorage.getItem(READ_STATE_STORAGE_KEY);
    expect(raw).toContain('"1"');
    expect(raw).toContain('"2"');
    expect(window.sessionStorage.getItem(PENDING_SCROLL_READ_STORAGE_KEY)).toBeNull();
  });
});

describe("markNewsAsReadBatch", () => {
  afterEach(() => {
    window.localStorage.clear();
  });

  test("markNewsAsRead still writes a single id", () => {
    markNewsAsRead(42);
    const raw: string | null = window.localStorage.getItem(READ_STATE_STORAGE_KEY);
    expect(raw).toContain('"42"');
  });
});
