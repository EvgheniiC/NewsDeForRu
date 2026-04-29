import { expect, test } from "vitest";

import { describePipelinePartialFailure, formatHealthTime } from "./pipelineUi";

test("formatHealthTime returns em dash for null", () => {
  expect(formatHealthTime(null)).toBe("—");
});

test("describePipelinePartialFailure when ok false and no error", () => {
  expect(
    describePipelinePartialFailure({
      ok: false,
      error: null
    })
  ).toBe("Пайплайн завершился с ok: false");
});

test("describePipelinePartialFailure when error present", () => {
  expect(
    describePipelinePartialFailure({
      ok: false,
      error: "boom"
    })
  ).toBeNull();
});
