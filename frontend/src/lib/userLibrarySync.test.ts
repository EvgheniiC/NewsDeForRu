import { describe, expect, test } from "vitest";
import { applySavedRemoves, mergeLibraryEntries, type LibraryTimestampEntry } from "./userLibrarySync";
import type { LibrarySyncOp } from "./librarySyncQueue";

describe("mergeLibraryEntries", () => {
  test("keeps the newer timestamp per news id", () => {
    const merged: LibraryTimestampEntry[] = mergeLibraryEntries(
      [
        { newsId: 1, at: 100 },
        { newsId: 2, at: 200 },
      ],
      [
        { newsId: 2, at: 250 },
        { newsId: 3, at: 300 },
      ],
    );
    const byId: Record<number, number> = {};
    for (const entry of merged) {
      byId[entry.newsId] = entry.at;
    }
    expect(byId).toEqual({ 1: 100, 2: 250, 3: 300 });
  });
});

describe("applySavedRemoves", () => {
  test("drops an item when the remove is at least as new as the mark", () => {
    const next: LibraryTimestampEntry[] = applySavedRemoves(
      [
        { newsId: 1, at: 100 },
        { newsId: 2, at: 200 },
      ],
      [{ kind: "saved_remove", newsId: 1, at: 100 } satisfies LibrarySyncOp],
    );
    expect(next).toEqual([{ newsId: 2, at: 200 }]);
  });

  test("keeps an item when the remove is older than the mark", () => {
    const next: LibraryTimestampEntry[] = applySavedRemoves(
      [{ newsId: 1, at: 200 }],
      [{ kind: "saved_remove", newsId: 1, at: 150 } satisfies LibrarySyncOp],
    );
    expect(next).toEqual([{ newsId: 1, at: 200 }]);
  });
});
