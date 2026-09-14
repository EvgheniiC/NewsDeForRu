import { describe, expect, test, beforeEach } from "vitest";
import {
  listUsefulEntries,
  listUsefulMarkedNewsIds,
  readStoredUseful,
  setStoredUseful,
  USEFUL_RETENTION_MS,
  USEFUL_STATE_STORAGE_KEY,
  type UsefulStorageEntry
} from "./usefulStorage";

describe("usefulStorage", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("marks and reads useful news", () => {
    setStoredUseful(7, true);
    expect(readStoredUseful(7)).toBe(true);
    expect(listUsefulMarkedNewsIds()).toEqual([7]);
  });

  test("unmarking removes useful news", () => {
    setStoredUseful(7, true);
    setStoredUseful(7, false);
    expect(readStoredUseful(7)).toBe(false);
    expect(listUsefulMarkedNewsIds()).toEqual([]);
  });

  test("listUsefulEntries returns marked news with timestamps", () => {
    setStoredUseful(1, true);
    setStoredUseful(2, true);
    const entries: UsefulStorageEntry[] = listUsefulEntries();
    const ids: number[] = entries.map((entry: UsefulStorageEntry) => entry.newsId).sort((a: number, b: number) => a - b);
    expect(ids).toEqual([1, 2]);
    expect(entries.every((entry: UsefulStorageEntry) => entry.markedAt > 0)).toBe(true);
  });

  test("useful entries expire after retention window", () => {
    localStorage.setItem(
      USEFUL_STATE_STORAGE_KEY,
      JSON.stringify({ "9": { markedAt: Date.now() - USEFUL_RETENTION_MS - 1000 } })
    );
    expect(readStoredUseful(9)).toBe(false);
    expect(listUsefulMarkedNewsIds()).toEqual([]);
  });
});
