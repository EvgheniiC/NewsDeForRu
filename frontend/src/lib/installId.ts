const INSTALL_KEY: string = "nga_install_id";

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

/** Stable id of this Android install (localStorage). One person, one id. */
export function getInstallId(): string {
  try {
    const existing: string | null = window.localStorage.getItem(INSTALL_KEY);
    if (existing !== null && existing.length === 36) {
      return existing;
    }
    const created: string = randomUuid();
    window.localStorage.setItem(INSTALL_KEY, created);
    return created;
  } catch {
    return randomUuid();
  }
}
