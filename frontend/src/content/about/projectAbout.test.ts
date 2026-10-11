import { expect, test } from "vitest";

import { projectNewsNewestFirst, type ProjectNewsItem } from "./projectAbout";

const older: ProjectNewsItem = {
  id: "older",
  publishedAt: "2026-01-02T10:00:00+01:00",
  body: "Текст",
};

const newer: ProjectNewsItem = {
  id: "newer",
  publishedAt: "2026-03-04T18:30:00+01:00",
  body: "Текст",
};

test("projectNewsNewestFirst sorts timestamps descending", (): void => {
  expect(projectNewsNewestFirst([older, newer]).map((item: ProjectNewsItem) => item.id)).toEqual([
    "newer",
    "older",
  ]);
});
