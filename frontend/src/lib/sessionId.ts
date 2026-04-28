const SESSION_KEY: string = "nga_session_id";

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

/** Per-tab session id (sessionStorage). */
export function getSessionId(): string {
  try {
    const existing: string | null = window.sessionStorage.getItem(SESSION_KEY);
    if (existing !== null && existing.length >= 8) {
      return existing;
    }
    const created: string = randomUuid();
    window.sessionStorage.setItem(SESSION_KEY, created);
    return created;
  } catch {
    return randomUuid();
  }
}
