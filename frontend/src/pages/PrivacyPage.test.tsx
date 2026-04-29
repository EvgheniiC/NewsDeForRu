import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { PrivacyPage } from "./PrivacyPage";

test("PrivacyPage renders main heading", () => {
  render(<PrivacyPage />);
  expect(screen.getByRole("heading", { level: 1 }).textContent).toContain("Конфиденциальность");
});
