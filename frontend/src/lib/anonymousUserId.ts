const STORAGE_KEY: string = "nga_anonymous_user_id";

function randomUuid(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c: string) => {
    const r: number = (Math.random() * 16) | 0;
    const v: number = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/** Stable anonymous profile id (localStorage). */
export function getAnonymousUserId(): string {
  try {
    const existing: string | null = window.localStorage.getItem(STORAGE_KEY);
    if (existing !== null && existing.length === 36) {
      return existing;
    }
    const created: string = randomUuid();
    window.localStorage.setItem(STORAGE_KEY, created);
    return created;
  } catch {
    return randomUuid();
  }
}
