import { App } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";
import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { appPathFromDeepLink } from "./appPathFromDeepLink";
import { markDeepLinkLaunchProcessed, wasDeepLinkLaunchProcessed } from "./deepLinkLaunchSession";

function currentAppPath(): string {
  return `${window.location.pathname}${window.location.search}${window.location.hash}`;
}

/** Handles Android App Links / iOS Universal Links: navigates SPA when the app opens from an https URL. */
export function DeepLinkListener(): null {
  const navigate = useNavigate();

  useEffect((): (() => void) | void => {
    if (!Capacitor.isNativePlatform()) {
      return;
    }

    const go = (url: string, source: "launch" | "open"): void => {
      if (source === "launch" && wasDeepLinkLaunchProcessed()) {
        return;
      }

      const path: string | null = appPathFromDeepLink(url);
      if (path === null || path === currentAppPath()) {
        if (source === "launch") {
          markDeepLinkLaunchProcessed();
        }
        return;
      }

      if (source === "launch") {
        markDeepLinkLaunchProcessed();
      }

      // Keep the feed route in history so "← Лента" and the system back button work.
      navigate(path, { replace: false });
    };

    let cancelled: boolean = false;
    let removeListener: (() => Promise<void>) | undefined;

    void (async (): Promise<void> => {
      const launch = await App.getLaunchUrl();
      if (cancelled) {
        return;
      }
      if (launch?.url) {
        go(launch.url, "launch");
      }
      const handle = await App.addListener("appUrlOpen", (event: { url: string }): void => {
        go(event.url, "open");
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
