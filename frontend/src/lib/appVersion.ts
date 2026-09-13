import { App } from "@capacitor/app";

/** Version baked into the web bundle (Vite define from package.json, or VITE_APP_VERSION). */
export function getBundledAppVersion(): string {
  return __APP_VERSION__;
}

/**
 * Installed native versionName when Capacitor can read it; otherwise the bundled version.
 * On Android this is what Play Store and system App info show.
 */
export async function loadInstalledAppVersion(): Promise<string> {
  try {
    const info: { version: string } = await App.getInfo();
    const nativeVersion: string = info.version.trim();
    if (nativeVersion.length > 0) {
      return nativeVersion;
    }
  } catch {
    /* jsdom / web without a native package */
  }
  return getBundledAppVersion();
}
