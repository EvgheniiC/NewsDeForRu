import { describe, expect, it } from "vitest";
import { planExternalUrlOpen } from "./openExternalUrl";

describe("planExternalUrlOpen", (): void => {
  it("opens the original article in a new tab on the website", (): void => {
    expect(planExternalUrlOpen("https://www.welt.de/article", false)).toEqual({
      url: "https://www.welt.de/article",
      leaveWebView: false,
    });
  });

  it("leaves the Android WebView instead of reloading the current news", (): void => {
    expect(planExternalUrlOpen(" https://www.bild.de/article ", true)).toEqual({
      url: "https://www.bild.de/article",
      leaveWebView: true,
    });
  });

  it("does nothing when the article URL is missing", (): void => {
    expect(planExternalUrlOpen("  ", true)).toBeNull();
  });
});
