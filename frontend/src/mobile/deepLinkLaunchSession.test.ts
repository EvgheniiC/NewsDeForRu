import { afterEach, describe, expect, it } from "vitest";
import { markDeepLinkLaunchProcessed, wasDeepLinkLaunchProcessed } from "./deepLinkLaunchSession";

describe("deepLinkLaunchSession", (): void => {
  afterEach((): void => {
    sessionStorage.clear();
  });

  it("returns false until launch is marked processed", (): void => {
    expect(wasDeepLinkLaunchProcessed()).toBe(false);
    markDeepLinkLaunchProcessed();
    expect(wasDeepLinkLaunchProcessed()).toBe(true);
  });
});
