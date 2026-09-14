import { beforeEach, describe, expect, test } from "vitest";
import {
  enqueueLibraryOp,
  listLibrarySyncOps,
} from "./librarySyncQueue";

describe("librarySyncQueue", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("keeps the latest remove per news id", () => {
    enqueueLibraryOp({ kind: "saved_remove", newsId: 7, at: 10 });
    enqueueLibraryOp({ kind: "saved_remove", newsId: 7, at: 20 });
    enqueueLibraryOp({ kind: "saved_remove", newsId: 8, at: 15 });
    expect(listLibrarySyncOps()).toEqual([
      { kind: "saved_remove", newsId: 7, at: 20 },
      { kind: "saved_remove", newsId: 8, at: 15 },
    ]);
  });
});
