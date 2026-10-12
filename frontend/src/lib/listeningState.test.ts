import { beforeEach, describe, expect, test } from "vitest";
import {
  enqueueNews,
  ensurePlaying,
  markFinished,
  nextUnfinishedId,
  readListeningState,
  removeNews,
  writeListeningState,
  type ListeningState,
  emptyListeningState,
} from "./listeningState";

describe("listening queue", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  test("keeps order and drops the oldest finished item past the limit", () => {
    let state: ListeningState = emptyListeningState();
    for (let newsId: number = 1; newsId <= 50; newsId += 1) {
      state = enqueueNews(state, newsId, newsId);
      if (newsId === 1) {
        state = markFinished(state, 1, 51);
      }
    }
    state = enqueueNews(state, 51, 60);
    expect(state.items).toHaveLength(50);
    expect(state.items.some((item: { newsId: number }) => item.newsId === 1)).toBe(false);
    expect(state.items[state.items.length - 1]?.newsId).toBe(51);
  });

  test("restarts a finished item and continues with the next unfinished one", () => {
    let state: ListeningState = enqueueNews(emptyListeningState(), 4, 1);
    state = enqueueNews(state, 9, 2);
    state = ensurePlaying(state, 4, 3, 2);
    state = markFinished(state, 4, 4);
    expect(nextUnfinishedId(state)).toBe(9);
    const again: ListeningState = ensurePlaying(state, 4, 5, 2);
    const restarted: { newsId: number; chunkIndex: number; finished: boolean } | undefined = again.items.find(
      (item: { newsId: number }) => item.newsId === 4,
    );
    expect(restarted?.chunkIndex).toBe(0);
    expect(restarted?.finished).toBe(false);
  });

  test("round-trips through local storage", () => {
    const state: ListeningState = removeNews(
      enqueueNews(emptyListeningState(), 3, 10),
      8,
      11,
    );
    writeListeningState({
      ...state,
      items: [{ newsId: 3, chunkIndex: 1, finished: false }],
      currentNewsId: 3,
      autoNext: true,
      updatedAt: 12,
    });
    expect(readListeningState()).toEqual({
      items: [{ newsId: 3, chunkIndex: 1, finished: false }],
      currentNewsId: 3,
      autoNext: true,
      updatedAt: 12,
    });
  });
});
