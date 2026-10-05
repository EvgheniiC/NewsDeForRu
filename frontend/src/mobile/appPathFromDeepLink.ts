const APP_LINK_HOSTS: ReadonlySet<string> = new Set<string>([
  "simplenewsapp.de",
  "www.simplenewsapp.de",
]);

/**
 * Returns an in-app path for React Router, or null when the URL should not trigger navigation.
 * Only this app's own https links are accepted. A publisher article must stay in the browser.
 */
export function appPathFromDeepLink(url: string): string | null {
  try {
    const parsed: URL = new URL(url);
    if (parsed.protocol !== "https:" && parsed.protocol !== "http:") {
      return null;
    }
    if (!APP_LINK_HOSTS.has(parsed.hostname.toLowerCase())) {
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
