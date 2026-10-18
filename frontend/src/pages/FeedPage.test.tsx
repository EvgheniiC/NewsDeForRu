import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

vi.mock("@capacitor/core", () => ({
  Capacitor: {
    isNativePlatform: (): boolean => false,
    getPlatform: (): string => "web"
  }
}));

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: null
  })
}));

vi.mock("../hooks/useInfiniteFeed", () => ({
  useInfiniteFeed: () => ({
    items: [],
    loading: false,
    loadingMore: false,
    feedError: "",
    nextCursor: null,
    reload: async (): Promise<void> => {},
    loadMore: async (): Promise<void> => {}
  })
}));

vi.mock("../hooks/useReadSavedFeed", () => ({
  useReadSavedFeed: () => ({
    items: [],
    loading: false,
    feedError: "",
    refresh: async (): Promise<void> => {}
  })
}));

vi.mock("../hooks/useUsefulSavedFeed", () => ({
  useUsefulSavedFeed: () => ({
    items: [],
    loading: false,
    feedError: "",
    refresh: async (): Promise<void> => {}
  })
}));

import { FeedPage } from "./FeedPage";

afterEach((): void => {
  cleanup();
});

test("empty economy and politics tabs stay and explain why there are few cards", () => {
  render(
    <MemoryRouter>
      <FeedPage />
    </MemoryRouter>
  );

  const economyTab: HTMLElement = screen.getByRole("tab", { name: "Экономика" });
  const politicsTab: HTMLElement = screen.getByRole("tab", { name: "Политика" });

  fireEvent.click(economyTab);
  expect(screen.getByText("В «Экономике» пока пусто.")).toBeTruthy();
  expect(screen.getByText(/Destatis и Eurostat/)).toBeTruthy();
  expect(economyTab.getAttribute("aria-selected")).toBe("true");

  fireEvent.click(politicsTab);
  expect(screen.getByText("В «Политике» пока пусто.")).toBeTruthy();
  expect(screen.getByText(/официальные сообщения/)).toBeTruthy();
  expect(politicsTab.getAttribute("aria-selected")).toBe("true");
  expect(screen.getByRole("tab", { name: "Экономика" })).toBeTruthy();
});
