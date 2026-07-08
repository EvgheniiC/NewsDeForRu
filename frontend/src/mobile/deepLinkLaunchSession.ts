const LAUNCH_PROCESSED_KEY: string = "deeplink:launch-processed";

/** Whether the cold-start launch URL was already applied in this browser session. */
export function wasDeepLinkLaunchProcessed(): boolean {
  try {
    return sessionStorage.getItem(LAUNCH_PROCESSED_KEY) === "1";
  } catch {
    return false;
  }
}

/** Remember that the cold-start launch URL must not be re-applied after reload/remount. */
export function markDeepLinkLaunchProcessed(): void {
  try {
    sessionStorage.setItem(LAUNCH_PROCESSED_KEY, "1");
  } catch {
    // sessionStorage may be unavailable in some WebViews
  }
}
