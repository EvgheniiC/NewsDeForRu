import { Capacitor } from "@capacitor/core";
import { isNewsRead, markNewsAsReadBatch } from "./readStateStorage";

export const PENDING_SCROLL_READ_STORAGE_KEY: string = "nga_scroll_read_pending_v1";

/** Web-only: scrolled-past news is marked read when the user leaves the feed. */
export function isWebScrollToReadEnabled(): boolean {
  return !Capacitor.isNativePlatform();
}

function readPendingIds(): number[] {
  try {
    const raw: string | null = window.sessionStorage.getItem(PENDING_SCROLL_READ_STORAGE_KEY);
    if (raw === null || raw === "") {
      return [];
    }
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    const ids: number[] = [];
    for (const value of parsed) {
      const id: number = typeof value === "number" ? value : Number.parseInt(String(value), 10);
      if (Number.isFinite(id)) {
        ids.push(id);
      }
    }
    return ids;
  } catch {
    return [];
  }
}

function writePendingIds(ids: number[]): void {
  try {
    if (ids.length === 0) {
      window.sessionStorage.removeItem(PENDING_SCROLL_READ_STORAGE_KEY);
      return;
    }
    window.sessionStorage.setItem(PENDING_SCROLL_READ_STORAGE_KEY, JSON.stringify(ids));
  } catch {
    /* storage full or disabled */
  }
}

export function queueScrollPastNews(newsId: number): void {
  if (!Number.isFinite(newsId) || isNewsRead(newsId)) {
    return;
  }
  const pending: number[] = readPendingIds();
  if (pending.includes(newsId)) {
    return;
  }
  writePendingIds([...pending, newsId]);
}

export function listPendingScrollReadIds(): number[] {
  return readPendingIds();
}

export function flushPendingScrollRead(): void {
  const pending: number[] = readPendingIds();
  if (pending.length === 0) {
    return;
  }
  writePendingIds([]);
  markNewsAsReadBatch(pending);
}
