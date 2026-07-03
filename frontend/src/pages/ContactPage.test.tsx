import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { AuthProvider } from "../context/AuthContext";
import { ContactPage } from "./ContactPage";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: (): boolean => false,
    getPlatform: (): string => "web",
  },
}));

function renderContact(): void {
  render(
    <MemoryRouter initialEntries={["/contact"]}>
      <AuthProvider>
        <ContactPage />
      </AuthProvider>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("ContactPage renders feedback form section", () => {
  renderContact();
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Контакты");
  expect(screen.getByRole("heading", { level: 2, name: "Обратная связь" })).toBeTruthy();
  expect(screen.getByLabelText("Сообщение")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Отправить" })).toBeTruthy();
});
