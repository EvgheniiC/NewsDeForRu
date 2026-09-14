import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { afterEach, expect, test, vi } from "vitest";

afterEach(() => {
  vi.resetModules();
  vi.doUnmock("@capacitor/app");
});

const frontendRoot: string = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

function readPackageVersion(): string {
  const raw: string = readFileSync(path.join(frontendRoot, "package.json"), "utf8");
  const parsed: { version: string } = JSON.parse(raw) as { version: string };
  return parsed.version;
}

function readAndroidVersionName(): string {
  const gradle: string = readFileSync(path.join(frontendRoot, "android/app/build.gradle"), "utf8");
  const match: RegExpMatchArray | null = gradle.match(/versionName\s+"([^"]+)"/);
  if (match === null || match[1] === undefined) {
    throw new Error("versionName not found in android/app/build.gradle");
  }
  return match[1];
}

test("getBundledAppVersion returns the injected app version", async () => {
  const { getBundledAppVersion } = await import("./appVersion");
  expect(getBundledAppVersion().length).toBeGreaterThan(0);
});

test("AAB versionName matches package.json and Impressum bundled version", async () => {
  const { getBundledAppVersion } = await import("./appVersion");
  const packageVersion: string = readPackageVersion();
  const androidVersionName: string = readAndroidVersionName();
  const impressumVersion: string = getBundledAppVersion();
  expect(androidVersionName).toBe(packageVersion);
  expect(impressumVersion).toBe(packageVersion);
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
