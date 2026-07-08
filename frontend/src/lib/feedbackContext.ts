import { Capacitor } from "@capacitor/core";

export interface FeedbackClientContext {
  pageUrl: string;
  platform: string;
  appVersion: string;
}

export function collectFeedbackClientContext(pageUrl: string): FeedbackClientContext {
  const platform: string = Capacitor.isNativePlatform() ? Capacitor.getPlatform() : "web";
  const appVersion: string =
    typeof import.meta.env.VITE_APP_VERSION === "string" && import.meta.env.VITE_APP_VERSION.trim().length > 0
      ? import.meta.env.VITE_APP_VERSION.trim()
      : "1.1.6";
  return {
    pageUrl,
    platform,
    appVersion,
  };
}
