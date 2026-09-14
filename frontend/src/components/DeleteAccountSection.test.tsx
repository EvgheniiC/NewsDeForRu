import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { DeleteAccountSection } from "./DeleteAccountSection";

const { deleteAccount } = vi.hoisted(() => {
  return { deleteAccount: vi.fn() };
});

vi.mock("../context/AuthContext", () => ({
  useAuth: (): { deleteAccount: typeof deleteAccount; user: { can_moderate: boolean } } => ({
    deleteAccount,
    user: { can_moderate: false },
  }),
}));

afterEach(() => {
  cleanup();
  deleteAccount.mockReset();
});

test("DeleteAccountSection asks for a password before deleting", () => {
  render(<DeleteAccountSection onDeleted={() => undefined} />);

  fireEvent.click(screen.getByRole("button", { name: "Удалить аккаунт" }));
  expect(screen.getByLabelText("Пароль для подтверждения")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Удалить навсегда" })).toBeTruthy();
  expect(deleteAccount).not.toHaveBeenCalled();
});
