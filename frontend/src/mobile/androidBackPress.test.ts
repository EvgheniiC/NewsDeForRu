import { describe, expect, it, vi } from "vitest";
import {
  FEED_PATH,
  applyAndroidBackPressAction,
  canNavigateBackInHistory,
  resolveAndroidBackPressAction,
} from "./androidBackPress";

describe("resolveAndroidBackPressAction", (): void => {
  it("returns consumed when an overlay handled the press", (): void => {
    expect(resolveAndroidBackPressAction("/news/1", true, true)).toEqual({ type: "consumed" });
  });

  it("navigates back from a nested page when history allows it", (): void => {
    expect(resolveAndroidBackPressAction("/news/1", true, false)).toEqual({
      type: "navigate",
      delta: -1,
    });
  });

  it("returns to feed when nested page has no browser history", (): void => {
    expect(resolveAndroidBackPressAction("/news/1", false, false)).toEqual({
      type: "replace",
      path: FEED_PATH,
    });
  });

  it("minimizes the app from the feed", (): void => {
    expect(resolveAndroidBackPressAction(FEED_PATH, false, false)).toEqual({ type: "minimize" });
  });
});

describe("applyAndroidBackPressAction", (): void => {
  it("calls navigate(-1) for history back", (): void => {
    const navigate = vi.fn();
    applyAndroidBackPressAction({ type: "navigate", delta: -1 }, navigate, vi.fn());
    expect(navigate).toHaveBeenCalledWith(-1);
  });

  it("calls minimizeApp on feed", (): void => {
    const minimizeApp = vi.fn();
    applyAndroidBackPressAction({ type: "minimize" }, vi.fn(), minimizeApp);
    expect(minimizeApp).toHaveBeenCalledOnce();
  });
});

describe("canNavigateBackInHistory", (): void => {
  it("returns true when React Router history index is above zero", (): void => {
    vi.spyOn(window.history, "state", "get").mockReturnValue({ idx: 2 });
    expect(canNavigateBackInHistory()).toBe(true);
  });

  it("returns false when history index is zero", (): void => {
    vi.spyOn(window.history, "state", "get").mockReturnValue({ idx: 0 });
    expect(canNavigateBackInHistory()).toBe(false);
  });
});
