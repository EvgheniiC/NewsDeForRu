import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, test } from "vitest";

import { LegalLocaleProvider } from "../context/LegalLocaleContext";
import { ImpressumPage } from "./ImpressumPage";

beforeEach(() => {
  localStorage.clear();
  localStorage.setItem("nga_legal_locale", "de");
});

afterEach(() => {
  cleanup();
});

test("ImpressumPage renders German heading", () => {
  render(
    <LegalLocaleProvider>
      <ImpressumPage />
    </LegalLocaleProvider>
  );
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Impressum");
});
