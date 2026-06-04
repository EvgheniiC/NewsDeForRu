import { beforeEach, describe, expect, it, vi } from "vitest";

import { enqueueOne } from "./engagementQueue";
import { grantAnalyticsConsent } from "../lib/analyticsConsent";

vi.mock("../api/client", () => ({
  postEngagementBatch: vi.fn(),
  ApiError: class ApiError extends Error {},
  NetworkError: class NetworkError extends Error {},
}));

describe("engagementQueue consent gate", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("does not enqueue without consent", () => {
    enqueueOne(1, "open_preview", { feed_mode: "grid" }, true);
    expect(localStorage.getItem("nga_analytics_consent")).toBeNull();
  });

  it("enqueues after grant", () => {
    grantAnalyticsConsent();
    enqueueOne(1, "open_preview", { feed_mode: "grid" }, true);
    expect(localStorage.getItem("nga_analytics_consent")).toBe("granted");
  });
});
