import { Capacitor } from "@capacitor/core";

import { getBundledAppVersion } from "./appVersion";

export interface FeedbackClientContext {
  pageUrl: string;
  platform: string;
  appVersion: string;
}

export function collectFeedbackClientContext(pageUrl: string): FeedbackClientContext {
  const platform: string = Capacitor.isNativePlatform() ? Capacitor.getPlatform() : "web";
  return {
    pageUrl,
    platform,
    appVersion: getBundledAppVersion(),
  };
}
