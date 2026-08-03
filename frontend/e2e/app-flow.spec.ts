import { expect, test } from "@playwright/test";
import { installApiMock } from "./fixtures/apiMock";

test.describe("end-to-end", () => {
  test("мобильная карточка полностью показывает кнопку раскрытия", async ({ page }) => {
    await page.setViewportSize({ width: 360, height: 568 });
    await installApiMock(page, {
      title: "Очень длинный заголовок новости, который занимает сразу несколько строк на мобильном экране",
      subtitle:
        "Длинное описание новости занимает много места, но не должно выталкивать нижнюю панель действий за границы карточки.",
    });
    await page.goto("/");

    const button = page.getByRole("button", { name: "Раскрыть" }).first();
    await expect(button).toBeVisible();

    const fitsInsideCard: boolean = await button.evaluate((element: HTMLElement): boolean => {
      const buttonRect: DOMRect = element.getBoundingClientRect();
      const card: HTMLElement | null = element.closest(".news-card");
      if (card === null) {
        return false;
      }
      const cardRect: DOMRect = card.getBoundingClientRect();
      return (
        buttonRect.top >= cardRect.top &&
        buttonRect.left >= cardRect.left &&
        buttonRect.right <= cardRect.right &&
        buttonRect.bottom <= cardRect.bottom
      );
    });
    expect(fitsInsideCard).toBe(true);
  });

  test("прямая ссылка на новость → назад в ленту", async ({ page }) => {
    await installApiMock(page);
    await page.goto("/news/1");

    await expect(page.getByRole("heading", { name: "E2E Test News" })).toBeVisible();
    await page.getByRole("button", { name: "← Лента" }).click();

    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "Новости простыми словами" })).toBeVisible();
    await expect(page.getByText("E2E Test News").first()).toBeVisible();
  });

  test("лента → раскрытие в карточке → вход → модерация (Publish)", async ({ page }) => {
    await installApiMock(page);
    await page.goto("/");

    await expect(page.getByRole("heading", { name: "Новости простыми словами" })).toBeVisible();
    await expect(page.getByText("E2E Test News").first()).toBeVisible();
    await expect(page.getByText("Загрузка ленты…")).not.toBeVisible({ timeout: 15_000 });

    await page.getByRole("button", { name: "Раскрыть" }).first().click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.getByRole("heading", { name: "Что это значит с разных сторон" })).toBeVisible();
    await expect(page.getByText("тестовый текст перспективы 2.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Свернуть" }).first()).toBeVisible();

    await page.getByRole("button", { name: "Меню" }).click();
    await page.getByRole("menuitem", { name: "Войти" }).click();
    await expect(page.getByRole("heading", { name: "Аккаунт" })).toBeVisible();
    await page.getByLabel(/Email для входа/i).fill("e2e@test.local");
    await page.getByLabel(/Пароль для входа/i).fill("e2e-secret");
    await page.getByRole("button", { name: "Войти" }).click();

    await page.getByRole("button", { name: "Меню аккаунта" }).click();
    await expect(page.getByRole("menuitem", { name: "Модерация" })).toBeVisible({ timeout: 15_000 });
    await page.getByRole("menuitem", { name: "Модерация" }).click();

    await expect(page.getByRole("heading", { name: "Модерация" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Publish" })).toBeVisible();

    await page.getByRole("button", { name: "Publish" }).click();
    await expect(page.getByText("Очередь пуста.")).toBeVisible();
  });
});
