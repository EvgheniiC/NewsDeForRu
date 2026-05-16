import type { CapacitorConfig } from "@capacitor/cli";

const config: CapacitorConfig = {
  appId: "de.simplenewsapp.app",
  appName: "newsForGermanyRU",
  webDir: "dist",
  server: {
    androidScheme: "https"
  }
};

export default config;
