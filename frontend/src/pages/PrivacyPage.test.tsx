import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test } from "vitest";

import { LegalLocaleProvider } from "../context/LegalLocaleContext";
import { PrivacyPage } from "./PrivacyPage";

function renderPrivacy(): void {
  render(
    <LegalLocaleProvider>
      <PrivacyPage />
    </LegalLocaleProvider>
  );
}

beforeEach(() => {
  localStorage.clear();
});

afterEach(() => {
  cleanup();
});

test("PrivacyPage renders German heading when locale is de", () => {
  localStorage.setItem("nga_legal_locale", "de");
  renderPrivacy();
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Datenschutzerklärung");
});

test("PrivacyPage renders Russian heading when locale is ru", () => {
  localStorage.setItem("nga_legal_locale", "ru");
  renderPrivacy();
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Политика конфиденциальности");
});
