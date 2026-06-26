import { expect, test } from "vitest";

import { APP_TIME_ZONE, formatDateRuBerlin, formatDateTimeRuBerlin } from "./dateTimeBerlin";

test("APP_TIME_ZONE is Berlin", () => {
  expect(APP_TIME_ZONE).toBe("Europe/Berlin");
});

test("formatDateTimeRuBerlin returns em dash for nullish", () => {
  expect(formatDateTimeRuBerlin(null)).toBe("—");
  expect(formatDateTimeRuBerlin(undefined)).toBe("—");
  expect(formatDateTimeRuBerlin("")).toBe("—");
});

test("formatDateRuBerlin formats date without time", () => {
  const out: string = formatDateRuBerlin("2026-04-30T16:01:38.000Z");
  expect(out).toMatch(/2026/);
  expect(out).not.toMatch(/:/);
});

test("formatDateTimeRuBerlin formats fixed UTC instant in Berlin wall time", () => {
  // 16:01 UTC on 2026-04-30 = 18:01 in Berlin (CEST)
  const out: string = formatDateTimeRuBerlin("2026-04-30T16:01:38.000Z");
  expect(out).toMatch(/30\.04\.2026/);
  expect(out).toMatch(/18:01:38/);
});
