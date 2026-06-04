import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  denyAnalyticsConsent,
  getAnalyticsConsent,
  getAnalyticsConsentRecordedAt,
  grantAnalyticsConsent,
  hasAnalyticsConsent,
  revokeAnalyticsConsent,
  subscribeAnalyticsConsent,
} from "./analyticsConsent";

const STORAGE_KEY: string = "nga_analytics_consent";
const ANON_KEY: string = "nga_anonymous_user_id";

describe("analyticsConsent", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it("starts unset", () => {
    expect(getAnalyticsConsent()).toBeNull();
    expect(hasAnalyticsConsent()).toBe(false);
  });

  it("grant enables analytics consent", () => {
    grantAnalyticsConsent();
    expect(getAnalyticsConsent()).toBe("granted");
    expect(hasAnalyticsConsent()).toBe(true);
    expect(getAnalyticsConsentRecordedAt()).not.toBeNull();
  });

  it("deny stores denied and clears anonymous id", () => {
    localStorage.setItem(ANON_KEY, "00000000-0000-4000-8000-000000000000");
    denyAnalyticsConsent();
    expect(getAnalyticsConsent()).toBe("denied");
    expect(localStorage.getItem(ANON_KEY)).toBeNull();
  });

  it("revoke clears choice so banner can show again", () => {
    grantAnalyticsConsent();
    revokeAnalyticsConsent();
    expect(getAnalyticsConsent()).toBeNull();
    expect(hasAnalyticsConsent()).toBe(false);
  });

  it("notifies subscribers on change", () => {
    const listener = vi.fn();
    const unsub = subscribeAnalyticsConsent(listener);
    grantAnalyticsConsent();
    expect(listener).toHaveBeenCalled();
    unsub();
    localStorage.removeItem(STORAGE_KEY);
  });
});
