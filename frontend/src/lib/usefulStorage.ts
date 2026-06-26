/** localStorage map of useful news IDs with timestamps (retention: 60 days). */

export const USEFUL_STATE_STORAGE_KEY: string = "nga_useful_state_v1";

/** Legacy per-id keys ``nga_useful_<newsId>`` → ``"1"`` / ``"0"``. */
export const USEFUL_STORAGE_PREFIX: string = "nga_useful_";

export const USEFUL_STORAGE_CHANGED_EVENT: string = "nga:useful-storage-changed";

export const USEFUL_RETENTION_MS: number = 60 * 24 * 60 * 60 * 1000;

interface UsefulStateEntry {
  markedAt: number;
}

type UsefulStateMap = Record<string, UsefulStateEntry>;

let legacyMigrationDone: boolean = false;

function readStateMap(): UsefulStateMap {
  try {
    const raw: string | null = window.localStorage.getItem(USEFUL_STATE_STORAGE_KEY);
    if (raw === null || raw === "") {
      return {};
    }
    const parsed: unknown = JSON.parse(raw);
    if (typeof parsed !== "object" || parsed === null || Array.isArray(parsed)) {
      return {};
    }
    return parsed as UsefulStateMap;
  } catch {
    return {};
  }
}

function writeStateMap(map: UsefulStateMap): void {
  try {
    window.localStorage.setItem(USEFUL_STATE_STORAGE_KEY, JSON.stringify(map));
  } catch {
    /* storage full or disabled */
  }
}

function purgeExpiredEntries(map: UsefulStateMap): UsefulStateMap {
  const cutoff: number = Date.now() - USEFUL_RETENTION_MS;
  const next: UsefulStateMap = {};
  for (const [key, entry] of Object.entries(map)) {
    if (entry.markedAt >= cutoff) {
      next[key] = entry;
    }
  }
  return next;
}

function migrateLegacyUsefulKeys(map: UsefulStateMap): UsefulStateMap {
  if (legacyMigrationDone) {
    return map;
  }
  legacyMigrationDone = true;

  const next: UsefulStateMap = { ...map };
  let changed: boolean = false;

  try {
    for (let i: number = 0; i < window.localStorage.length; i += 1) {
      const key: string | null = window.localStorage.key(i);
      if (key === null || !key.startsWith(USEFUL_STORAGE_PREFIX) || key === USEFUL_STATE_STORAGE_KEY) {
        continue;
      }
      const suffix: string = key.slice(USEFUL_STORAGE_PREFIX.length);
      const id: number = Number.parseInt(suffix, 10);
      if (!Number.isFinite(id)) {
        continue;
      }
      const value: string | null = window.localStorage.getItem(key);
      window.localStorage.removeItem(key);
      if (value === "1" && next[String(id)] === undefined) {
        next[String(id)] = { markedAt: Date.now() };
        changed = true;
      }
    }
  } catch {
    return map;
  }

  return changed ? purgeExpiredEntries(next) : map;
}

function loadActiveMap(): UsefulStateMap {
  const raw: UsefulStateMap = readStateMap();
  const migrated: UsefulStateMap = migrateLegacyUsefulKeys(raw);
  const purged: UsefulStateMap = purgeExpiredEntries(migrated);
  if (JSON.stringify(raw) !== JSON.stringify(purged)) {
    writeStateMap(purged);
  }
  return purged;
}

export function notifyUsefulStorageChanged(): void {
  try {
    window.dispatchEvent(new Event(USEFUL_STORAGE_CHANGED_EVENT));
  } catch {
    /* ignore */
  }
}

export function setStoredUseful(newsId: number, useful: boolean): void {
  if (!Number.isFinite(newsId)) {
    return;
  }
  const map: UsefulStateMap = loadActiveMap();
  const key: string = String(newsId);
  if (useful) {
    map[key] = { markedAt: Date.now() };
  } else {
    delete map[key];
  }
  writeStateMap(purgeExpiredEntries(map));
  notifyUsefulStorageChanged();
}

export function readStoredUseful(newsId: number): boolean {
  const entry: UsefulStateEntry | undefined = loadActiveMap()[String(newsId)];
  if (entry === undefined) {
    return false;
  }
  return entry.markedAt >= Date.now() - USEFUL_RETENTION_MS;
}

export function listUsefulMarkedNewsIds(): number[] {
  const map: UsefulStateMap = loadActiveMap();
  const ids: number[] = [];
  for (const [key] of Object.entries(map)) {
    const id: number = Number.parseInt(key, 10);
    if (!Number.isFinite(id)) {
      continue;
    }
    if (readStoredUseful(id)) {
      ids.push(id);
    }
  }
  ids.sort((a: number, b: number) => {
    const aAt: number = map[String(a)]?.markedAt ?? 0;
    const bAt: number = map[String(b)]?.markedAt ?? 0;
    return bAt - aAt;
  });
  return ids;
}
