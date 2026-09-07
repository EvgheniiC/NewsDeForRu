import { expect, test } from "vitest";

import { parseOptionalBooleanEnv } from "./envFlags";

test("parseOptionalBooleanEnv reads typical flag tokens", (): void => {
  expect(parseOptionalBooleanEnv("true")).toBe(true);
  expect(parseOptionalBooleanEnv("1")).toBe(true);
  expect(parseOptionalBooleanEnv("false")).toBe(false);
  expect(parseOptionalBooleanEnv("0")).toBe(false);
  expect(parseOptionalBooleanEnv(undefined)).toBeUndefined();
  expect(parseOptionalBooleanEnv("maybe")).toBeUndefined();
});
