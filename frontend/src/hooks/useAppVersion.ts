import { useEffect, useState } from "react";

import { getBundledAppVersion, loadInstalledAppVersion } from "../lib/appVersion";

/** Bundled version immediately; replaced by the native package version on Android. */
export function useAppVersion(): string {
  const [version, setVersion] = useState<string>(getBundledAppVersion());

  useEffect(() => {
    let cancelled: boolean = false;
    void loadInstalledAppVersion().then((installed: string) => {
      if (!cancelled) {
        setVersion(installed);
      }
    });
    return (): void => {
      cancelled = true;
    };
  }, []);

  return version;
}
