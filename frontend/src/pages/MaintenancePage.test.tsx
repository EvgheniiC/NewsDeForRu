import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test } from "vitest";

import { LegalLocaleProvider } from "../context/LegalLocaleContext";
import { MaintenancePage } from "./MaintenancePage";

beforeEach((): void => {
  localStorage.clear();
  localStorage.setItem("nga_legal_locale", "de");
});

afterEach((): void => {
  cleanup();
});

test("MaintenancePage renders German reconstruction copy", (): void => {
  render(
    <MemoryRouter>
      <LegalLocaleProvider>
        <MaintenancePage />
      </LegalLocaleProvider>
    </MemoryRouter>,
  );

  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Website in Überarbeitung");
  expect(screen.getByRole("link", { name: "Impressum" })).toBeTruthy();
  expect(screen.getByRole("link", { name: "Datenschutz" })).toBeTruthy();
  expect(screen.getByRole("link", { name: "Kontakt" })).toBeTruthy();
  expect(document.title).toBe("Überarbeitung — newsForGermanyRU");
  expect(document.head.querySelector('meta[name="robots"]')?.getAttribute("content")).toBe(
    "noindex, nofollow",
  );
});
