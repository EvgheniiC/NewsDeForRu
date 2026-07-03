/** localStorage map of read news IDs with timestamps (retention: 30 days). */

export const READ_STATE_STORAGE_KEY: string = "nga_read_state_v1";

export const READ_STATE_CHANGED_EVENT: string = "nga:read-state-changed";

export const READ_RETENTION_MS: number = 30 * 24 * 60 * 60 * 1000;

interface ReadStateEntry {
  readAt: number;
}

type ReadStateMap = Record<string, ReadStateEntry>;

function readStateMap(): ReadStateMap {
  try {
    const raw: string | null = window.localStorage.getItem(READ_STATE_STORAGE_KEY);
    if (raw === null || raw === "") {
      return {};
    }
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      return {};
    }
    return parsed as ReadStateMap;
  } catch {
    return {};
  }
}

function writeStateMap(map: ReadStateMap): void {
  try {
    window.localStorage.setItem(READ_STATE_STORAGE_KEY, JSON.stringify(map));
  } catch {
    /* storage full or disabled */
  }
}

function purgeExpiredEntries(map: ReadStateMap): ReadStateMap {
  const cutoff: number = Date.now() - READ_RETENTION_MS;
  const next: ReadStateMap = {};
  for (const [key, entry] of Object.entries(map)) {
    if (entry.readAt >= cutoff) {
      next[key] = entry;
    }
  }
  return next;
}

export function notifyReadStateChanged(): void {
  try {
    window.dispatchEvent(new Event(READ_STATE_CHANGED_EVENT));
  } catch {
    /* ignore */
  }
}

export function markNewsAsRead(newsId: number): void {
  markNewsAsReadBatch([newsId]);
}

export function markNewsAsReadBatch(newsIds: readonly number[]): void {
  const uniqueIds: number[] = [];
  for (const newsId of newsIds) {
    if (!Number.isFinite(newsId)) {
      continue;
    }
    if (!uniqueIds.includes(newsId)) {
      uniqueIds.push(newsId);
    }
  }
  if (uniqueIds.length === 0) {
    return;
  }
  const now: number = Date.now();
  const map: ReadStateMap = purgeExpiredEntries(readStateMap());
  for (const newsId of uniqueIds) {
    map[String(newsId)] = { readAt: now };
  }
  writeStateMap(map);
  notifyReadStateChanged();
}

export function isNewsRead(newsId: number): boolean {
  const entry: ReadStateEntry | undefined = readStateMap()[String(newsId)];
  if (entry === undefined) {
    return false;
  }
  if (entry.readAt < Date.now() - READ_RETENTION_MS) {
    return false;
  }
  return true;
}

export function getNewsReadAt(newsId: number): number | null {
  const entry: ReadStateEntry | undefined = readStateMap()[String(newsId)];
  if (entry === undefined || entry.readAt < Date.now() - READ_RETENTION_MS) {
    return null;
  }
  return entry.readAt;
}

export function listReadNewsIds(): number[] {
  const map: ReadStateMap = purgeExpiredEntries(readStateMap());
  const ids: number[] = [];
  for (const [key, entry] of Object.entries(map)) {
    const id: number = Number.parseInt(key, 10);
    if (!Number.isFinite(id)) {
      continue;
    }
    ids.push(id);
  }
  ids.sort((a: number, b: number) => {
    const aAt: number = map[String(a)]?.readAt ?? 0;
    const bAt: number = map[String(b)]?.readAt ?? 0;
    return bAt - aAt;
  });
  return ids;
}
