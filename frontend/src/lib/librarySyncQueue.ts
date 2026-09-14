/** Persisted unsynced library mutations (needed so unmarks survive offline / logout). */

export const LIBRARY_SYNC_QUEUE_KEY: string = "nga_library_sync_queue_v1";

export type LibrarySyncOp =
  | { kind: "saved_remove"; newsId: number; at: number };

type LibrarySyncFlushHandler = () => Promise<void>;

const FLUSH_MS: number = 850;

let flushTimer: ReturnType<typeof setTimeout> | null = null;
let flushing: boolean = false;
let flushHandler: LibrarySyncFlushHandler | null = null;

function isSavedRemoveOp(value: unknown): value is LibrarySyncOp {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const rec: Record<string, unknown> = value as Record<string, unknown>;
  return rec.kind === "saved_remove" && typeof rec.newsId === "number" && typeof rec.at === "number";
}

export function listLibrarySyncOps(): LibrarySyncOp[] {
  try {
    const raw: string | null = window.localStorage.getItem(LIBRARY_SYNC_QUEUE_KEY);
    if (raw === null || raw === "") {
      return [];
    }
    const parsed: unknown = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    const ops: LibrarySyncOp[] = [];
    for (const item of parsed) {
      if (isSavedRemoveOp(item) && Number.isFinite(item.newsId) && Number.isFinite(item.at)) {
        ops.push({ kind: "saved_remove", newsId: item.newsId, at: item.at });
      }
    }
    return ops;
  } catch {
    return [];
  }
}

export function replaceLibrarySyncOps(ops: readonly LibrarySyncOp[]): void {
  try {
    if (ops.length === 0) {
      window.localStorage.removeItem(LIBRARY_SYNC_QUEUE_KEY);
      return;
    }
    window.localStorage.setItem(LIBRARY_SYNC_QUEUE_KEY, JSON.stringify(ops));
  } catch {
    /* storage full or disabled */
  }
}

export function clearLibrarySyncOps(): void {
  replaceLibrarySyncOps([]);
}

export function enqueueLibraryOp(op: LibrarySyncOp): void {
  const current: LibrarySyncOp[] = listLibrarySyncOps();
  const next: LibrarySyncOp[] = current.filter((item: LibrarySyncOp) => item.newsId !== op.newsId);
  next.push(op);
  replaceLibrarySyncOps(next);
  scheduleLibrarySyncFlush();
}

export function setLibrarySyncFlushHandler(handler: LibrarySyncFlushHandler | null): void {
  flushHandler = handler;
  if (handler !== null) {
    scheduleLibrarySyncFlush();
  }
}

export function scheduleLibrarySyncFlush(): void {
  if (flushHandler === null) {
    return;
  }
  if (flushTimer !== null) {
    return;
  }
  flushTimer = window.setTimeout(() => {
    flushTimer = null;
    void flushLibrarySyncQueue();
  }, FLUSH_MS);
}

export async function flushLibrarySyncQueue(): Promise<void> {
  if (flushHandler === null || flushing) {
    return;
  }
  flushing = true;
  try {
    await flushHandler();
  } finally {
    flushing = false;
    if (flushHandler !== null && listLibrarySyncOps().length > 0 && flushTimer === null) {
      scheduleLibrarySyncFlush();
    }
  }
}

export function opKey(op: LibrarySyncOp): string {
  return `${op.kind}:${op.newsId}:${op.at}`;
}
