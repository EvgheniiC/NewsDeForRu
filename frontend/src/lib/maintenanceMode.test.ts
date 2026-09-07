import { expect, test } from "vitest";

import { isMaintenanceExemptPath, resolveMaintenanceMode } from "./maintenanceMode";

test("resolveMaintenanceMode stays off on native apps", (): void => {
  expect(
    resolveMaintenanceMode({ isNative: true, isProd: true, envValue: "true" }),
  ).toBe(false);
});

test("resolveMaintenanceMode follows explicit env on web", (): void => {
  expect(
    resolveMaintenanceMode({ isNative: false, isProd: false, envValue: "true" }),
  ).toBe(true);
  expect(
    resolveMaintenanceMode({ isNative: false, isProd: true, envValue: "false" }),
  ).toBe(false);
});

test("resolveMaintenanceMode closes production web when env is unset", (): void => {
  expect(
    resolveMaintenanceMode({ isNative: false, isProd: true, envValue: undefined }),
  ).toBe(true);
  expect(
    resolveMaintenanceMode({ isNative: false, isProd: false, envValue: undefined }),
  ).toBe(false);
});

test("isMaintenanceExemptPath keeps legal and staff routes", (): void => {
  expect(isMaintenanceExemptPath("/")).toBe(false);
  expect(isMaintenanceExemptPath("/news/12")).toBe(false);
  expect(isMaintenanceExemptPath("/impressum")).toBe(true);
  expect(isMaintenanceExemptPath("/privacy")).toBe(true);
  expect(isMaintenanceExemptPath("/contact")).toBe(true);
  expect(isMaintenanceExemptPath("/login")).toBe(true);
  expect(isMaintenanceExemptPath("/account/reset")).toBe(true);
  expect(isMaintenanceExemptPath("/moderation")).toBe(true);
});
