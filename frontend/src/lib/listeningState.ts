/** Listen queue stored on the device. The server copy uses the same fields in snake_case. */

import type { UserListeningState } from "../types/userListening";

export const LISTENING_STATE_KEY: string = "nga_listening_state_v1";
export const LISTENING_OWNER_KEY: string = "nga_listening_owner_user_id";
export const LISTENING_STATE_EVENT: string = "nga-listening-state";

export const MAX_LISTEN_QUEUE: number = 50;

export interface ListenQueueItem {
  newsId: number;
  chunkIndex: number;
  finished: boolean;
}

export interface ListeningState {
  items: ListenQueueItem[];
  currentNewsId: number | null;
  autoNext: boolean;
  updatedAt: number;
}

export function emptyListeningState(): ListeningState {
  return { items: [], currentNewsId: null, autoNext: false, updatedAt: 0 };
}

function isQueueItem(value: unknown): value is ListenQueueItem {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const rec: Record<string, unknown> = value as Record<string, unknown>;
  return (
    typeof rec.newsId === "number" &&
    Number.isFinite(rec.newsId) &&
    rec.newsId > 0 &&
    typeof rec.chunkIndex === "number" &&
    Number.isFinite(rec.chunkIndex) &&
    rec.chunkIndex >= 0 &&
    typeof rec.finished === "boolean"
  );
}

export function sanitizeListeningState(value: unknown): ListeningState {
  if (typeof value !== "object" || value === null) {
    return emptyListeningState();
  }
  const rec: Record<string, unknown> = value as Record<string, unknown>;
  const items: ListenQueueItem[] = [];
  if (Array.isArray(rec.items)) {
    for (const item of rec.items) {
      if (isQueueItem(item)) {
        items.push({
          newsId: item.newsId,
          chunkIndex: Math.min(Math.floor(item.chunkIndex), 500),
          finished: item.finished,
        });
      }
      if (items.length >= MAX_LISTEN_QUEUE) {
        break;
      }
    }
  }
  const currentRaw: unknown = rec.currentNewsId;
  const currentNewsId: number | null =
    typeof currentRaw === "number" && Number.isFinite(currentRaw) && currentRaw > 0 ? currentRaw : null;
  const updatedRaw: unknown = rec.updatedAt;
  const updatedAt: number =
    typeof updatedRaw === "number" && Number.isFinite(updatedRaw) && updatedRaw >= 0 ? updatedRaw : 0;
  const keptIds: Set<number> = new Set(items.map((item: ListenQueueItem) => item.newsId));
  return {
    items,
    currentNewsId: currentNewsId !== null && keptIds.has(currentNewsId) ? currentNewsId : null,
    autoNext: rec.autoNext === true,
    updatedAt,
  };
}

export function readListeningState(): ListeningState {
  try {
    const raw: string | null = window.localStorage.getItem(LISTENING_STATE_KEY);
    if (raw === null || raw === "") {
      return emptyListeningState();
    }
    return sanitizeListeningState(JSON.parse(raw));
  } catch {
    return emptyListeningState();
  }
}

export function writeListeningState(state: ListeningState): void {
  const next: string = JSON.stringify(sanitizeListeningState(state));
  try {
    const prev: string | null = window.localStorage.getItem(LISTENING_STATE_KEY);
    if (prev === next) {
      return;
    }
    window.localStorage.setItem(LISTENING_STATE_KEY, next);
    window.dispatchEvent(new Event(LISTENING_STATE_EVENT));
  } catch {
    /* storage full or disabled */
  }
}

export function clearListeningState(): void {
  try {
    window.localStorage.removeItem(LISTENING_STATE_KEY);
    window.dispatchEvent(new Event(LISTENING_STATE_EVENT));
  } catch {
    /* ignore */
  }
}

export function readListeningOwner(): number | null {
  try {
    const raw: string | null = window.localStorage.getItem(LISTENING_OWNER_KEY);
    if (raw === null || raw === "") {
      return null;
    }
    const parsed: number = Number.parseInt(raw, 10);
    if (!Number.isFinite(parsed)) {
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export function writeListeningOwner(userId: number): void {
  try {
    window.localStorage.setItem(LISTENING_OWNER_KEY, String(userId));
  } catch {
    /* storage full or disabled */
  }
}

export function clearListeningOwner(): void {
  try {
    window.localStorage.removeItem(LISTENING_OWNER_KEY);
  } catch {
    /* ignore */
  }
}

function trimQueue(items: readonly ListenQueueItem[], currentNewsId: number | null): ListenQueueItem[] {
  const next: ListenQueueItem[] = [...items];
  while (next.length > MAX_LISTEN_QUEUE) {
    const finishedIndex: number = next.findIndex(
      (item: ListenQueueItem) => item.finished && item.newsId !== currentNewsId,
    );
    if (finishedIndex >= 0) {
      next.splice(finishedIndex, 1);
      continue;
    }
    const oldestOther: number = next.findIndex((item: ListenQueueItem) => item.newsId !== currentNewsId);
    if (oldestOther >= 0) {
      next.splice(oldestOther, 1);
      continue;
    }
    next.shift();
  }
  return next;
}

export function enqueueNews(state: ListeningState, newsId: number, now: number): ListeningState {
  if (state.items.some((item: ListenQueueItem) => item.newsId === newsId)) {
    return state;
  }
  return {
    ...state,
    items: trimQueue([...state.items, { newsId, chunkIndex: 0, finished: false }], state.currentNewsId),
    updatedAt: now,
  };
}

export function removeNews(state: ListeningState, newsId: number, now: number): ListeningState {
  const items: ListenQueueItem[] = state.items.filter((item: ListenQueueItem) => item.newsId !== newsId);
  return {
    ...state,
    items,
    currentNewsId: state.currentNewsId === newsId ? null : state.currentNewsId,
    updatedAt: now,
  };
}

export function ensurePlaying(
  state: ListeningState,
  newsId: number,
  now: number,
  chunkCount: number,
): ListeningState {
  const existing: ListenQueueItem | undefined = state.items.find(
    (item: ListenQueueItem) => item.newsId === newsId,
  );
  let items: ListenQueueItem[];
  if (existing === undefined) {
    items = trimQueue([...state.items, { newsId, chunkIndex: 0, finished: false }], newsId);
  } else {
    const restart: boolean = existing.finished || existing.chunkIndex >= chunkCount;
    items = state.items.map((item: ListenQueueItem) =>
      item.newsId === newsId
        ? { ...item, finished: false, chunkIndex: restart ? 0 : existing.chunkIndex }
        : item,
    );
  }
  return { ...state, items, currentNewsId: newsId, updatedAt: now };
}

export function setChunk(state: ListeningState, newsId: number, chunkIndex: number, now: number): ListeningState {
  return {
    ...state,
    currentNewsId: newsId,
    updatedAt: now,
    items: state.items.map((item: ListenQueueItem) =>
      item.newsId === newsId ? { ...item, chunkIndex, finished: false } : item,
    ),
  };
}

export function markFinished(state: ListeningState, newsId: number, now: number): ListeningState {
  return {
    ...state,
    updatedAt: now,
    items: state.items.map((item: ListenQueueItem) =>
      item.newsId === newsId ? { ...item, finished: true } : item,
    ),
  };
}

export function nextUnfinishedId(state: ListeningState): number | null {
  if (state.items.length === 0) {
    return null;
  }
  const start: number = state.items.findIndex((item: ListenQueueItem) => item.newsId === state.currentNewsId);
  const ordered: ListenQueueItem[] =
    start < 0 ? [...state.items] : [...state.items.slice(start + 1), ...state.items.slice(0, start)];
  const next: ListenQueueItem | undefined = ordered.find((item: ListenQueueItem) => !item.finished);
  return next?.newsId ?? null;
}

export function toApiListeningState(state: ListeningState): UserListeningState {
  const clean: ListeningState = sanitizeListeningState(state);
  return {
    items: clean.items.map((item: ListenQueueItem) => ({
      news_id: item.newsId,
      chunk_index: item.chunkIndex,
      finished: item.finished,
    })),
    current_news_id: clean.currentNewsId,
    auto_next: clean.autoNext,
    updated_at: clean.updatedAt,
  };
}

export function fromApiListeningState(state: UserListeningState): ListeningState {
  return sanitizeListeningState({
    items: state.items.map((item: UserListeningState["items"][number]) => ({
      newsId: item.news_id,
      chunkIndex: item.chunk_index,
      finished: item.finished,
    })),
    currentNewsId: state.current_news_id,
    autoNext: state.auto_next,
    updatedAt: state.updated_at,
  });
}
