import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { GOOGLE_PLAY_APP_URL, projectGoalParagraphs } from "../content/about/projectAbout";
import { AboutPage } from "./AboutPage";

afterEach((): void => {
  cleanup();
});

test("AboutPage shows the project goal and the latest updates", (): void => {
  render(<AboutPage />);

  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("О проекте");
  expect(screen.getByRole("heading", { level: 2, name: "Новости проекта" })).toBeTruthy();
  expect(screen.getByText(projectGoalParagraphs[0] ?? "")).toBeTruthy();
  expect(screen.getByText("18 октября 2026 г. в 19:24")).toBeTruthy();
  expect(
    screen.getByText("Добавили аудиопрослушивание новостей. Слушать можно только после регистрации."),
  ).toBeTruthy();
  expect(screen.getByText("11 октября 2026 г. в 19:15")).toBeTruthy();

  const playLink: HTMLAnchorElement = screen.getByRole("link", { name: "Google Play" });
  expect(playLink.getAttribute("href")).toBe(GOOGLE_PLAY_APP_URL);
  expect(playLink.textContent).toBe("Google Play");
});
