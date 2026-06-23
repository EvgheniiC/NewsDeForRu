import type { Page, Route } from "@playwright/test";

const MOCK_API: string = "http://127.0.0.1:8000";

const corsHeaders: Readonly<Record<string, string>> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

const jsonHeaders: Readonly<Record<string, string>> = {
  ...corsHeaders,
  "Content-Type": "application/json; charset=utf-8",
};

async function fulfillJson(route: Route, data: unknown, status: number = 200): Promise<void> {
  await route.fulfill({
    status,
    headers: { ...jsonHeaders },
    body: JSON.stringify(data),
  });
}

function bearerPresent(route: Route): boolean {
  const headers = route.request().headers();
  const raw =
    typeof headers.authorization === "string"
      ? headers.authorization
      : typeof headers.Authorization === "string"
        ? headers.Authorization
        : "";
  return raw.trim().toLowerCase().startsWith("bearer ");
}

/**
 * Mocks the backend (default `VITE_API_BASE_URL` = http://127.0.0.1:8000).
 * Stateful moderation queue: first GET returns one item, after approve GET returns [].
 */
export async function installApiMock(page: Page): Promise<void> {
  const feedItem: Record<string, unknown> = {
    id: 1,
    title: "E2E Test News",
    subtitle: "Тестовый подзаголовок",
    read_time_minutes: 2,
    topic: "life",
    is_urgent: false,
    is_positive: false,
    created_at: "2024-01-15T10:00:00",
  };

  const processedBody: Record<string, unknown> = {
    id: 1,
    title: "E2E Test News",
    one_sentence_summary: "Кратко о новости E2E.",
    plain_language: "Простое объяснение для теста.",
    impact_presentation: "multi",
    impact_unified: "",
    impact_owner: "Если вы на стороне бизнеса: тестовый текст перспективы 1.",
    impact_tenant: "Если вы потребитель в быту: тестовый текст перспективы 2.",
    impact_buyer: "Если вы рассматриваете крупную покупку: тестовый текст перспективы 3.",
    action_items: "Проверить сценарий E2E.",
    bonus_block: "Бонус.",
    spoiler: "Спойлер.",
    source_url: "https://example.com/e2e",
    confidence_score: 0.9,
    publication_status: "needs_review",
    read_time_minutes: 2,
    topic: "life",
    is_urgent: false,
    is_positive: false,
    created_at: "2024-01-15T10:00:00",
  };

  let queue: Record<string, unknown>[] = [processedBody];

  await page.route(`${MOCK_API}/**`, async (route: Route) => {
    if (route.request().method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: { ...corsHeaders } });
      return;
    }

    const url: URL = new URL(route.request().url());
    const method: string = route.request().method();
    const path: string = url.pathname;

    if (path === "/auth/register" && method === "POST") {
      await fulfillJson(route, {
        detail: "Check your email to confirm your account.",
      });
      return;
    }

    if (path === "/auth/verify-email" && method === "POST") {
      await fulfillJson(route, {
        access_token: "e2e-access-token-mock",
        refresh_token: "e2e-refresh-token-mock",
        token_type: "bearer",
      });
      return;
    }

    if (path === "/auth/resend-verification" && method === "POST") {
      await fulfillJson(route, {
        detail: "If this email is registered and not yet confirmed, you will receive a verification link shortly.",
      });
      return;
    }

    if (path === "/auth/login" && method === "POST") {
      await fulfillJson(route, {
        access_token: "e2e-access-token-mock",
        refresh_token: "e2e-refresh-token-mock",
        token_type: "bearer",
      });
      return;
    }

    if (path === "/auth/refresh" && method === "POST") {
      await fulfillJson(route, {
        access_token: "e2e-access-token-mock-refreshed",
        refresh_token: "e2e-refresh-token-mock-rotated",
        token_type: "bearer",
      });
      return;
    }

    if (path === "/auth/logout" && method === "POST") {
      await fulfillJson(route, { detail: "ok" });
      return;
    }

    if (path === "/auth/forgot-password" && method === "POST") {
      await fulfillJson(route, {
        detail: "If this email is registered, you will receive password reset instructions shortly.",
      });
      return;
    }

    if (path === "/auth/reset-password" && method === "POST") {
      await fulfillJson(route, { detail: "Password updated. You can sign in with the new password." });
      return;
    }

    if (path === "/auth/me" && method === "GET") {
      if (!bearerPresent(route)) {
        await fulfillJson(route, { detail: "Not authenticated" }, 401);
        return;
      }
      await fulfillJson(route, {
        id: 1,
        email: "e2e@test.local",
        role: "admin",
        can_moderate: true,
        can_run_pipeline: true,
      });
      return;
    }

    if (path === "/health" && method === "GET") {
      await fulfillJson(route, {
        status: "ok",
        database: "ok",
        last_pipeline_run_at: "2024-01-15T10:00:00Z",
        last_pipeline_ok: true,
        last_pipeline_run_id: null,
        pipeline_scheduler: "disabled",
      });
      return;
    }

    if (path === "/news" && method === "GET") {
      await fulfillJson(route, {
        items: [feedItem],
        next_cursor: null,
      });
      return;
    }

    if (path === "/news/top-today" && method === "GET") {
      await fulfillJson(route, {
        items: [
          {
            ...feedItem,
            rank: {
              total_score: 18,
              source_count: 2,
              mentions_points: 2,
              freshness_points: 3,
              ai_importance: 7,
            },
          },
        ],
      });
      return;
    }

    if (path === "/news/1" && method === "GET") {
      await fulfillJson(route, processedBody);
      return;
    }

    if (path === "/news/1/full-article" && method === "GET") {
      await fulfillJson(route, {
        news_id: 1,
        full_article_ru: "Полный текст статьи для E2E.",
        cached: true,
      });
      return;
    }

    if (path === "/moderation/queue" && method === "GET") {
      if (!bearerPresent(route)) {
        await fulfillJson(route, { detail: "Not authenticated" }, 401);
        return;
      }
      await fulfillJson(route, queue);
      return;
    }

    if (path === "/moderation/1/action" && method === "POST") {
      if (!bearerPresent(route)) {
        await fulfillJson(route, { detail: "Not authenticated" }, 401);
        return;
      }
      queue = [];
      const after: Record<string, unknown> = { ...processedBody, publication_status: "published" };
      await fulfillJson(route, after);
      return;
    }

    if (path === "/engagement/events" && method === "POST") {
      await fulfillJson(route, { inserted: 1, skipped_duplicate: 0 });
      return;
    }

    await route.fulfill({ status: 404, headers: { ...corsHeaders }, body: "Not mocked" });
  });
}
