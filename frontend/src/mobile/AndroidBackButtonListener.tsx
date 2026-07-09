import { App } from "@capacitor/app";
import { Capacitor } from "@capacitor/core";
import { useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { handleAndroidBackPress } from "./androidBackPress";

/** Handles the Android system back button in the Capacitor WebView. */
export function AndroidBackButtonListener(): null {
  const navigate = useNavigate();
  const { pathname } = useLocation();
  const pathnameRef = useRef<string>(pathname);

  pathnameRef.current = pathname;

  useEffect((): (() => void) | void => {
    if (!Capacitor.isNativePlatform() || Capacitor.getPlatform() !== "android") {
      return;
    }

    let cancelled: boolean = false;
    let removeListener: (() => Promise<void>) | undefined;

    void (async (): Promise<void> => {
      const handle = await App.addListener("backButton", (): void => {
        handleAndroidBackPress(pathnameRef.current, navigate, (): Promise<void> => App.minimizeApp());
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
