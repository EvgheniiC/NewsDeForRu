import { Capacitor } from "@capacitor/core";

export interface ExternalUrlOpenPlan {
  readonly url: string;
  /** Android WebView must leave the app. target="_blank" reloads the same news. */
  readonly leaveWebView: boolean;
}

/** Decide how a reader should leave the card for the original article. */
export function planExternalUrlOpen(url: string, nativeApp: boolean): ExternalUrlOpenPlan | null {
  const target: string = url.trim();
  if (target.length === 0) {
    return null;
  }
  return { url: target, leaveWebView: nativeApp };
}

/**
 * Open an original-article URL outside the current page.
 * On Android, assigning the location lets the WebView hand the URL to the system browser.
 */
export function openExternalUrl(url: string): void {
  const plan: ExternalUrlOpenPlan | null = planExternalUrlOpen(url, Capacitor.isNativePlatform());
  if (plan === null) {
    return;
  }
  if (plan.leaveWebView) {
    window.location.assign(plan.url);
    return;
  }
  window.open(plan.url, "_blank", "noopener,noreferrer");
}
