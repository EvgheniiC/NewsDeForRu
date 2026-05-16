import { App } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { appPathFromDeepLink } from "./appPathFromDeepLink";

/** Handles Android App Links / iOS Universal Links: navigates SPA when the app opens from an https URL. */
export function DeepLinkListener(): null {
  const navigate = useNavigate();

  useEffect((): (() => void) | void => {
    if (!Capacitor.isNativePlatform()) {
      return;
    }

    const go = (url: string): void => {
      const path: string | null = appPathFromDeepLink(url);
      if (path === null) {
        return;
      }
      navigate(path, { replace: true });
    };

    let cancelled: boolean = false;
    let removeListener: (() => Promise<void>) | undefined;

    void (async (): Promise<void> => {
      const launch = await App.getLaunchUrl();
      if (cancelled) {
        return;
      }
      if (launch?.url) {
        go(launch.url);
      }
      const handle = await App.addListener("appUrlOpen", (event: { url: string }): void => {
        go(event.url);
      });
      if (cancelled) {
        await handle.remove();
        return;
      }
      removeListener = async (): Promise<void> => {
        await handle.remove();
      };
    })();

    return (): void => {
      cancelled = true;
      void removeListener?.();
    };
  }, [navigate]);

  return null;
}
