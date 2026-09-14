import {
  getUserLibrary,
  putUserLibrary,
} from "../api/client";
import type {
  UserLibraryPutRequest,
  UserLibraryReadItem,
  UserLibrarySavedDelta,
  UserLibrarySnapshot,
} from "../types/userLibrary";
import {
  clearLibrarySyncOps,
  flushLibrarySyncQueue,
  listLibrarySyncOps,
  replaceLibrarySyncOps,
  setLibrarySyncFlushHandler,
  type LibrarySyncOp,
  opKey,
} from "./librarySyncQueue";
import { applyReadSnapshot, listReadEntries, type ReadStorageEntry } from "./readStateStorage";
import { applyUsefulSnapshot, listUsefulEntries, type UsefulStorageEntry } from "./usefulStorage";

export const LIBRARY_OWNER_STORAGE_KEY: string = "nga_library_owner_user_id";

export interface LibraryTimestampEntry {
  newsId: number;
  at: number;
}

function readLibraryOwner(): number | null {
  try {
    const raw: string | null = window.localStorage.getItem(LIBRARY_OWNER_STORAGE_KEY);
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

function writeLibraryOwner(userId: number): void {
  try {
    window.localStorage.setItem(LIBRARY_OWNER_STORAGE_KEY, String(userId));
  } catch {
    /* storage full or disabled */
  }
}

export function clearLibraryOwner(): void {
  try {
    window.localStorage.removeItem(LIBRARY_OWNER_STORAGE_KEY);
  } catch {
    /* ignore */
  }
}

export function mergeLibraryEntries(
  local: readonly LibraryTimestampEntry[],
  remote: readonly LibraryTimestampEntry[],
): LibraryTimestampEntry[] {
  const map: Map<number, number> = new Map();
  for (const entry of local) {
    map.set(entry.newsId, entry.at);
  }
  for (const entry of remote) {
    const current: number | undefined = map.get(entry.newsId);
    if (current === undefined || entry.at > current) {
      map.set(entry.newsId, entry.at);
    }
  }
  const out: LibraryTimestampEntry[] = [];
  for (const [newsId, at] of map.entries()) {
    out.push({ newsId, at });
  }
  return out;
}

export function applySavedRemoves(
  entries: readonly LibraryTimestampEntry[],
  removes: readonly LibrarySyncOp[],
): LibraryTimestampEntry[] {
  const map: Map<number, number> = new Map();
  for (const entry of entries) {
    map.set(entry.newsId, entry.at);
  }
  for (const op of removes) {
    const current: number | undefined = map.get(op.newsId);
    if (current === undefined || op.at >= current) {
      map.delete(op.newsId);
    }
  }
  const out: LibraryTimestampEntry[] = [];
  for (const [newsId, at] of map.entries()) {
    out.push({ newsId, at });
  }
  return out;
}

function toUsefulSnapshot(entries: readonly LibraryTimestampEntry[]): UsefulStorageEntry[] {
  return entries.map((entry: LibraryTimestampEntry) => ({ newsId: entry.newsId, markedAt: entry.at }));
}

function toReadSnapshot(entries: readonly LibraryTimestampEntry[]): ReadStorageEntry[] {
  return entries.map((entry: LibraryTimestampEntry) => ({ newsId: entry.newsId, readAt: entry.at }));
}

function snapshotToSavedEntries(snapshot: UserLibrarySnapshot): LibraryTimestampEntry[] {
  return snapshot.saved.map((item: UserLibrarySnapshot["saved"][number]) => ({
    newsId: item.news_id,
    at: item.marked_at,
  }));
}

function snapshotToReadEntries(snapshot: UserLibrarySnapshot): LibraryTimestampEntry[] {
  return snapshot.read.map((item: UserLibrarySnapshot["read"][number]) => ({
    newsId: item.news_id,
    at: item.read_at,
  }));
}

export async function flushUserLibraryToServer(accessToken: string): Promise<void> {
  const pending: LibrarySyncOp[] = listLibrarySyncOps();
  const savedEntries: UsefulStorageEntry[] = listUsefulEntries();
  const readEntries: ReadStorageEntry[] = listReadEntries();
  const saved: UserLibrarySavedDelta[] = savedEntries.map((entry: UsefulStorageEntry) => ({
    news_id: entry.newsId,
    marked_at: entry.markedAt,
    removed: false,
  }));
  for (const op of pending) {
    saved.push({ news_id: op.newsId, marked_at: op.at, removed: true });
  }
  const read: UserLibraryReadItem[] = readEntries.map((entry: ReadStorageEntry) => ({
    news_id: entry.newsId,
    read_at: entry.readAt,
  }));
  const payload: UserLibraryPutRequest = { saved, read };
  await putUserLibrary(accessToken, payload);
  const sentKeys: Set<string> = new Set(pending.map((op: LibrarySyncOp) => opKey(op)));
  const remaining: LibrarySyncOp[] = listLibrarySyncOps().filter(
    (op: LibrarySyncOp) => !sentKeys.has(opKey(op)),
  );
  replaceLibrarySyncOps(remaining);
}

export async function reconcileUserLibrary(accessToken: string, userId: number): Promise<void> {
  const snapshot: UserLibrarySnapshot = await getUserLibrary(accessToken);
  const owner: number | null = readLibraryOwner();
  const remoteSaved: LibraryTimestampEntry[] = snapshotToSavedEntries(snapshot);
  const remoteRead: LibraryTimestampEntry[] = snapshotToReadEntries(snapshot);

  if (owner !== null && owner !== userId) {
    applyUsefulSnapshot(toUsefulSnapshot(remoteSaved));
    applyReadSnapshot(toReadSnapshot(remoteRead));
    clearLibrarySyncOps();
    writeLibraryOwner(userId);
    await flushUserLibraryToServer(accessToken);
    return;
  }

  const pending: LibrarySyncOp[] = listLibrarySyncOps();
  const mergedSaved: LibraryTimestampEntry[] = applySavedRemoves(
    mergeLibraryEntries(
      listUsefulEntries().map((entry: UsefulStorageEntry) => ({ newsId: entry.newsId, at: entry.markedAt })),
      remoteSaved,
    ),
    pending,
  );
  const mergedRead: LibraryTimestampEntry[] = mergeLibraryEntries(
    listReadEntries().map((entry: ReadStorageEntry) => ({ newsId: entry.newsId, at: entry.readAt })),
    remoteRead,
  );
  applyUsefulSnapshot(toUsefulSnapshot(mergedSaved));
  applyReadSnapshot(toReadSnapshot(mergedRead));
  writeLibraryOwner(userId);
  await flushUserLibraryToServer(accessToken);
}

export function configureUserLibrarySync(options: {
  userId: number | null;
  runAuthenticated: ((task: (accessToken: string) => Promise<void>) => Promise<void>) | null;
}): () => void {
  if (options.userId === null || options.runAuthenticated === null) {
    setLibrarySyncFlushHandler(null);
    return (): void => undefined;
  }
  const userId: number = options.userId;
  const runAuthenticated: (task: (accessToken: string) => Promise<void>) => Promise<void> =
    options.runAuthenticated;
  setLibrarySyncFlushHandler(async (): Promise<void> => {
    await runAuthenticated(async (accessToken: string): Promise<void> => {
      await flushUserLibraryToServer(accessToken);
    });
  });
  void runAuthenticated(async (accessToken: string): Promise<void> => {
    await reconcileUserLibrary(accessToken, userId);
  });
  const flushNow = (): void => {
    void flushLibrarySyncQueue();
  };
  const onVisibility = (): void => {
    if (document.visibilityState === "hidden") {
      flushNow();
    }
  };
  window.addEventListener("visibilitychange", onVisibility);
  window.addEventListener("pagehide", flushNow);
  return (): void => {
    setLibrarySyncFlushHandler(null);
    window.removeEventListener("visibilitychange", onVisibility);
    window.removeEventListener("pagehide", flushNow);
  };
}
