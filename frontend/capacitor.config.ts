import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "de.simplenewsapp.app",
  appName: "newsForGermanyRU",
  webDir: "dist",
  server: {
    androidScheme: "https"
  },
  // Local dev API is usually http://10.0.2.2:8000 — without this, WebView blocks mixed content (https app → http API).
  android: {
    allowMixedContent: true
  }
};

export default config;
