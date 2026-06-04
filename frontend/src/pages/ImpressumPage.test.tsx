import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";

import { ImpressumPage } from "./ImpressumPage";

test("ImpressumPage renders main heading", () => {
  render(<ImpressumPage />);
  expect(screen.getByRole("heading", { level: 1 }).textContent).toBe("Impressum");
});
