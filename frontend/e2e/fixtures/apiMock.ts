import type { Page, Route } from "@playwright/test";

const MOCK_API: string = "http://127.0.0.1:8000";

const corsHeaders: Readonly<Record<string, string>> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS, HEAD",
  "Access-Control-Allow-Headers": "Content-Type, Authorization"
};

const jsonHeaders: Readonly<Record<string, string>> = {
  ...corsHeaders,
  "Content-Type": "application/json; charset=utf-8"
};

async function fulfillJson(route: Route, data: unknown, status: number = 200): Promise<void> {
  await route.fulfill({
    status,
    headers: { ...jsonHeaders },
    body: JSON.stringify(data)
  });
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
    created_at: "2024-01-15T10:00:00"
  };

  const processedBody: Record<string, unknown> = {
    id: 1,
    title: "E2E Test News",
    one_sentence_summary: "Кратко о новости E2E.",
    plain_language: "Простое объяснение для теста.",
    impact_owner: "Для владельца: текст.",
    impact_tenant: "Для арендатора: текст.",
    impact_buyer: "Для покупателя: текст.",
    action_items: "Проверить сценарий E2E.",
    bonus_block: "Бонус.",
    spoiler: "Спойлер.",
    source_url: "https://example.com/e2e",
    confidence_score: 0.9,
    publication_status: "needs_review",
    read_time_minutes: 2,
    topic: "life",
    is_urgent: false,
    created_at: "2024-01-15T10:00:00"
  };

  const impactTenant: Record<string, unknown> = { role: "tenant", text: "Твой сценарий: арендатор." };

  let queue: Record<string, unknown>[] = [processedBody];

  await page.route(`${MOCK_API}/**`, async (route: Route) => {
    if (route.request().method() === "OPTIONS") {
      await route.fulfill({ status: 204, headers: { ...corsHeaders } });
      return;
    }

    const url: URL = new URL(route.request().url());
    const method: string = route.request().method();
    const path: string = url.pathname;

    if (path === "/health" && method === "GET") {
      await fulfillJson(route, {
        status: "ok",
        database: "ok",
        last_pipeline_run_at: "2024-01-15T10:00:00Z",
        last_pipeline_ok: true,
        pipeline_scheduler: "disabled"
      });
      return;
    }

    if (path === "/news" && method === "GET") {
      await fulfillJson(route, [feedItem]);
      return;
    }

    if (path === "/news/1" && method === "GET") {
      await fulfillJson(route, processedBody);
      return;
    }

    if (path === "/news/1/impact" && method === "GET" && url.searchParams.get("role") === "tenant") {
      await fulfillJson(route, impactTenant);
      return;
    }

    if (path === "/moderation/queue" && method === "GET") {
      await fulfillJson(route, queue);
      return;
    }

    if (path === "/moderation/1/action" && method === "POST") {
      queue = [];
      const after: Record<string, unknown> = { ...processedBody, publication_status: "published" };
      await fulfillJson(route, after);
      return;
    }

    await route.fulfill({ status: 404, headers: { ...corsHeaders }, body: "Not mocked" });
  });
}
