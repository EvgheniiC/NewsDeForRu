import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

vi.mock("../api/client", () => ({
  ApiError: class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  },
  getModerationDailyStats: vi.fn(async () => ({
    date: "2026-10-12",
    published_count: 1,
    moderation_count: 2,
    visit_count: 3,
    download_count: 7,
  })),
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: { can_moderate: true },
    logout: async (): Promise<void> => {},
    withModerationAccess: async <T,>(run: (accessToken: string) => Promise<T>): Promise<T> =>
      run("token"),
  }),
}));

import { StatisticsPage } from "./StatisticsPage";

afterEach((): void => {
  cleanup();
});

test("StatisticsPage shows how many people installed the app", async (): Promise<void> => {
  render(
    <MemoryRouter>
      <StatisticsPage />
    </MemoryRouter>,
  );

  expect(await screen.findByText("Скачивания")).toBeTruthy();
  expect(await screen.findByText("7")).toBeTruthy();
  expect(
    screen.getByText(/Сколько человек установили Android-приложение/),
  ).toBeTruthy();
});
