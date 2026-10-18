import { expect, test } from "vitest";

import { feedEmptyStateCopy } from "./feedEmptyState";

test("economy and politics empty states explain why the tab has no cards", () => {
  const economy = feedEmptyStateCopy("economy");
  const politics = feedEmptyStateCopy("politics");

  expect(economy.lead).toContain("Экономике");
  expect(economy.detail).toContain("Destatis");
  expect(politics.lead).toContain("Политике");
  expect(politics.detail).toContain("официальные сообщения");
});

test("other empty feeds explain that only open sources are published", () => {
  const life = feedEmptyStateCopy("life");

  expect(life.lead).toBe("Пока нет новостей в этой подборке.");
  expect(life.detail).toContain("открытые источники");
  expect(feedEmptyStateCopy("urgent").lead).toContain("сделать сегодня");
});
