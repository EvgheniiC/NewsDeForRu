/** localStorage keys ``nga_useful_<newsId>`` → ``"1"`` / ``"0"`` (same-tab updates need a custom event). */

export const USEFUL_STORAGE_PREFIX: string = "nga_useful_";

export const USEFUL_STORAGE_CHANGED_EVENT: string = "nga:useful-storage-changed";

export function readStoredUseful(newsId: number): boolean {
  try {
    return window.localStorage.getItem(`${USEFUL_STORAGE_PREFIX}${newsId}`) === "1";
  } catch {
    return false;
  }
}

export function listUsefulMarkedNewsIds(): number[] {
  const ids: number[] = [];
  try {
    for (let i: number = 0; i < window.localStorage.length; i += 1) {
      const key: string | null = window.localStorage.key(i);
      if (key === null || !key.startsWith(USEFUL_STORAGE_PREFIX)) {
        continue;
      }
      const suffix: string = key.slice(USEFUL_STORAGE_PREFIX.length);
      const id: number = Number.parseInt(suffix, 10);
      if (!Number.isFinite(id)) {
        continue;
      }
      if (readStoredUseful(id)) {
        ids.push(id);
      }
    }
  } catch {
    return [];
  }
  return [...new Set(ids)].sort((a: number, b: number) => b - a);
}

export function notifyUsefulStorageChanged(): void {
  try {
    window.dispatchEvent(new Event(USEFUL_STORAGE_CHANGED_EVENT));
  } catch {
    /* ignore */
  }
}
