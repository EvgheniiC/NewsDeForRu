import { expect, test } from "@playwright/test";
import { installApiMock } from "./fixtures/apiMock";

test.describe("end-to-end", () => {
  test("лента → детали → модерация (Publish)", async ({ page }) => {
    await installApiMock(page);
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Объясняем новости" })).toBeVisible();
    await expect(page.getByText("E2E Test News").first()).toBeVisible();
    await expect(page.getByText("Загрузка ленты…")).not.toBeVisible({ timeout: 15_000 });

    await page.getByRole("link", { name: "Открыть" }).first().click();
    await expect(page).toHaveURL(/\/news\/1$/);
    await expect(page.getByRole("heading", { name: "E2E Test News" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Что это значит с разных сторон" })).toBeVisible();
    await expect(page.getByText("тестовый текст перспективы 2.")).toBeVisible();

    await page.getByRole("link", { name: "Модерация" }).click();
    await expect(page.getByRole("heading", { name: "Модерация" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Publish" })).toBeVisible();

    await page.getByRole("button", { name: "Publish" }).click();
    await expect(page.getByText("Очередь пуста.")).toBeVisible();
  });
});
