import { beforeEach, describe, expect, it, vi } from "vitest";

import { grantAnalyticsConsent } from "../lib/analyticsConsent";

const nativeState = vi.hoisted(() => ({ native: true, name: "android" }));
const postAppInstall = vi.hoisted(() => vi.fn(async () => ({ recorded: true })));

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: () => nativeState.native,
    getPlatform: () => nativeState.name,
  },
}));

vi.mock("../api/client", () => ({
  postAppInstall,
}));

import { recordAppInstallIfNeeded } from "./recordAppInstall";

describe("recordAppInstallIfNeeded", () => {
  beforeEach(() => {
    localStorage.clear();
    nativeState.native = true;
    nativeState.name = "android";
    postAppInstall.mockClear();
    postAppInstall.mockResolvedValue({ recorded: true });
  });

  it("does not report a web visit", async () => {
    nativeState.native = false;
    grantAnalyticsConsent();
    await recordAppInstallIfNeeded();
    expect(postAppInstall).not.toHaveBeenCalled();
  });

  it("does not report without analytics consent", async () => {
    await recordAppInstallIfNeeded();
    expect(postAppInstall).not.toHaveBeenCalled();
  });

  it("reports one Android install and skips the next open", async () => {
    grantAnalyticsConsent();
    await recordAppInstallIfNeeded();
    await recordAppInstallIfNeeded();
    expect(postAppInstall).toHaveBeenCalledTimes(1);
    const installId: string = String(postAppInstall.mock.calls[0]?.[0]);
    expect(installId).toHaveLength(36);
    expect(localStorage.getItem("nga_install_reported")).toBe("1");
  });
});
