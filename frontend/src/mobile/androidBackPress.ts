import type { NavigateFunction } from "react-router-dom";

export const FEED_PATH: string = "/";

export type AndroidBackPressHandler = () => boolean;

const overlayHandlers: Set<AndroidBackPressHandler> = new Set<AndroidBackPressHandler>();

/** Registers a handler that can consume the Android back press (e.g. close an overlay). */
export function registerAndroidBackPressHandler(handler: AndroidBackPressHandler): () => void {
  overlayHandlers.add(handler);
  return (): void => {
    overlayHandlers.delete(handler);
  };
}

export function consumeAndroidBackPress(): boolean {
  for (const handler of overlayHandlers) {
    if (handler()) {
      return true;
    }
  }
  return false;
}

export function canNavigateBackInHistory(): boolean {
  const idx: unknown = window.history.state?.idx;
  return typeof idx === "number" && idx > 0;
}

export type AndroidBackPressAction =
  | { type: "consumed" }
  | { type: "navigate"; delta: number }
  | { type: "replace"; path: string }
  | { type: "minimize" };

/** Pure navigation decision for the hardware back button (testable without Capacitor). */
export function resolveAndroidBackPressAction(
  pathname: string,
  canGoBack: boolean,
  overlayConsumed: boolean,
): AndroidBackPressAction {
  if (overlayConsumed) {
    return { type: "consumed" };
  }

  if (pathname !== FEED_PATH) {
    if (canGoBack) {
      return { type: "navigate", delta: -1 };
    }
    return { type: "replace", path: FEED_PATH };
  }

  return { type: "minimize" };
}

export function applyAndroidBackPressAction(
  action: AndroidBackPressAction,
  navigate: NavigateFunction,
  minimizeApp: () => void | Promise<void>,
): void {
  switch (action.type) {
    case "consumed":
      return;
    case "navigate":
      navigate(action.delta);
      return;
    case "replace":
      navigate(action.path, { replace: true });
      return;
    case "minimize":
      void minimizeApp();
      return;
  }
}

export function handleAndroidBackPress(pathname: string, navigate: NavigateFunction, minimizeApp: () => void | Promise<void>): void {
  const action: AndroidBackPressAction = resolveAndroidBackPressAction(
    pathname,
    canNavigateBackInHistory(),
    consumeAndroidBackPress(),
  );
  applyAndroidBackPressAction(action, navigate, minimizeApp);
}
