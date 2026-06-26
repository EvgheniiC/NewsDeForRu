import { describe, expect, test, beforeEach } from "vitest";
import {
  listUsefulMarkedNewsIds,
  readStoredUseful,
  setStoredUseful,
  USEFUL_RETENTION_MS,
  USEFUL_STATE_STORAGE_KEY
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

  test("useful entries expire after retention window", () => {
    localStorage.setItem(
      USEFUL_STATE_STORAGE_KEY,
      JSON.stringify({ "9": { markedAt: Date.now() - USEFUL_RETENTION_MS - 1000 } })
    );
    expect(readStoredUseful(9)).toBe(false);
    expect(listUsefulMarkedNewsIds()).toEqual([]);
  });
});
