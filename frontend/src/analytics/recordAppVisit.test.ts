import { beforeEach, describe, expect, it, vi } from "vitest";

import { grantAnalyticsConsent } from "../lib/analyticsConsent";

const nativeState = vi.hoisted(() => ({ native: false, name: "web" }));
const postAppVisit = vi.hoisted(() => vi.fn(async () => ({ recorded: true })));

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: () => nativeState.native,
    getPlatform: () => nativeState.name,
  },
}));

vi.mock("../api/client", () => ({
  postAppVisit,
}));

import { recordAppVisitIfNeeded } from "./recordAppVisit";

describe("recordAppVisitIfNeeded", () => {
  beforeEach(() => {
    localStorage.clear();
    sessionStorage.clear();
    nativeState.native = false;
    nativeState.name = "web";
    postAppVisit.mockClear();
    postAppVisit.mockResolvedValue({ recorded: true });
  });

  it("does not report without analytics consent", async () => {
    await recordAppVisitIfNeeded();
    expect(postAppVisit).not.toHaveBeenCalled();
  });

  it("reports one website visit per session", async () => {
    grantAnalyticsConsent();
    await recordAppVisitIfNeeded();
    await recordAppVisitIfNeeded();
    expect(postAppVisit).toHaveBeenCalledTimes(1);
    expect(postAppVisit.mock.calls[0]?.[1]).toBe("web");
  });

  it("reports an Android visit from the native app", async () => {
    nativeState.native = true;
    nativeState.name = "android";
    grantAnalyticsConsent();
    await recordAppVisitIfNeeded();
    expect(postAppVisit.mock.calls[0]?.[1]).toBe("android");
  });
});
