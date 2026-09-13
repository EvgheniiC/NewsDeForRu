import { afterEach, expect, test, vi } from "vitest";

afterEach(() => {
  vi.resetModules();
  vi.doUnmock("@capacitor/app");
});

test("getBundledAppVersion returns the injected app version", async () => {
  const { getBundledAppVersion } = await import("./appVersion");
  expect(getBundledAppVersion().length).toBeGreaterThan(0);
});

test("loadInstalledAppVersion prefers native package version", async () => {
  vi.doMock("@capacitor/app", () => ({
    App: {
      getInfo: async (): Promise<{ version: string }> => ({ version: "1.2.10" }),
    },
  }));
  const { loadInstalledAppVersion } = await import("./appVersion");
  await expect(loadInstalledAppVersion()).resolves.toBe("1.2.10");
});

test("loadInstalledAppVersion falls back when native version is empty", async () => {
  vi.doMock("@capacitor/app", () => ({
    App: {
      getInfo: async (): Promise<{ version: string }> => ({ version: "  " }),
    },
  }));
  const { getBundledAppVersion, loadInstalledAppVersion } = await import("./appVersion");
  await expect(loadInstalledAppVersion()).resolves.toBe(getBundledAppVersion());
});
