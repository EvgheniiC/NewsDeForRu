import { describe, expect, it } from "vitest";
import { appPathFromDeepLink } from "./appPathFromDeepLink";

describe("appPathFromDeepLink", (): void => {
  it("returns path for https news URL", (): void => {
    expect(appPathFromDeepLink("https://simplenewsapp.de/news/42")).toBe("/news/42");
  });

  it("includes search and hash on this app's host", (): void => {
    expect(appPathFromDeepLink("https://www.simplenewsapp.de/news/1?x=1#h")).toBe("/news/1?x=1#h");
  });

  it("ignores a publisher article so it is not opened as the same in-app news", (): void => {
    expect(appPathFromDeepLink("https://www.welt.de/politik/article")).toBeNull();
    expect(appPathFromDeepLink("https://example.com/news/1?x=1#h")).toBeNull();
  });

  it("returns null for root path", (): void => {
    expect(appPathFromDeepLink("https://simplenewsapp.de/")).toBeNull();
    expect(appPathFromDeepLink("https://simplenewsapp.de")).toBeNull();
  });

  it("returns null for non-http(s)", (): void => {
    expect(appPathFromDeepLink("myapp://news/1")).toBeNull();
  });
});
