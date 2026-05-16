/**
 * Returns an in-app path for React Router, or null when the URL should not trigger navigation.
 */
export function appPathFromDeepLink(url: string): string | null {
  try {
    const parsed: URL = new URL(url);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
      return null;
    }
    const path: string = `${parsed.pathname}${parsed.search}${parsed.hash}`;
    if (path === "" || path === "/") {
      return null;
    }
    return path;
  } catch {
    return null;
  }
}
