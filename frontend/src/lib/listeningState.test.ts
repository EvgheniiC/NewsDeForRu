import { beforeEach, describe, expect, test } from "vitest";
import {
  chooseListeningState,
  enqueueNews,
  ensurePlaying,
  markFinished,
  nextUnfinishedId,
  readListeningState,
  removeNews,
  setPosition,
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
    const restarted: { newsId: number; chunkIndex: number; charOffset: number; finished: boolean } | undefined =
      again.items.find((item: { newsId: number }) => item.newsId === 4);
    expect(restarted?.chunkIndex).toBe(0);
    expect(restarted?.charOffset).toBe(0);
    expect(restarted?.finished).toBe(false);
  });

  test("keeps a saved place when playback starts again before the item is finished", () => {
    let state: ListeningState = ensurePlaying(emptyListeningState(), 4, 1, 8);
    state = setPosition(state, 4, 3, 12, 2);
    const again: ListeningState = ensurePlaying(state, 4, 3, 2);
    const kept: { chunkIndex: number; charOffset: number } | undefined = again.items.find(
      (item: { newsId: number }) => item.newsId === 4,
    );
    expect(kept?.chunkIndex).toBe(3);
    expect(kept?.charOffset).toBe(12);
  });

  test("keeps the newer listen place when two copies disagree", () => {
    const older: ListeningState = setPosition(ensurePlaying(emptyListeningState(), 4, 1, 4), 4, 0, 0, 1);
    const newer: ListeningState = setPosition(older, 4, 2, 8, 9);
    expect(chooseListeningState(newer, older).items[0]?.chunkIndex).toBe(2);
    expect(chooseListeningState(older, newer).items[0]?.charOffset).toBe(8);
  });

  test("round-trips through local storage", () => {
    const state: ListeningState = removeNews(
      enqueueNews(emptyListeningState(), 3, 10),
      8,
      11,
    );
    writeListeningState({
      ...state,
      items: [{ newsId: 3, chunkIndex: 1, charOffset: 4, finished: false }],
      currentNewsId: 3,
      autoNext: true,
      updatedAt: 12,
    });
    expect(readListeningState()).toEqual({
      items: [{ newsId: 3, chunkIndex: 1, charOffset: 4, finished: false }],
      currentNewsId: 3,
      autoNext: true,
      updatedAt: 12,
    });
  });
});
