import type {
  UserLoginCredentials,
  UserMe,
  UserRegisterCredentials,
  UserTokenPair,
  RegisterResponse,
} from "../types/userAuth";
import type { EngagementBatchRequestBody, EngagementBatchResponseBody } from "../types/engagement";
import type { FullArticleResponse } from "../types/fullArticle";
import type { FeedPeriodKey, NewsFeedItem, NewsTopic, ProcessedNews } from "../types/news";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";

export const API_BASE_URL: string = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000"
).trim();

export class ApiError extends Error {
  public readonly status: number;

  constructor(message: string, status: number, options?: ErrorOptions) {
    super(message, options);
    this.name = "ApiError";
    this.status = status;
  }
}

/** Thrown when `fetch` fails (no HTTP response), e.g. DNS, offline, CORS. */
export class NetworkError extends Error {
  constructor(message: string, options?: ErrorOptions) {
    super(message, options);
    this.name = "NetworkError";
  }
}

async function fetchWithNetworkGuard(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_BASE_URL}${path}`, init);
  } catch (cause: unknown) {
    const message: string = cause instanceof Error ? cause.message : "Network request failed";
    throw new NetworkError(message, { cause });
  }
}

function parseJsonBody(text: string): unknown {
  if (!text.trim()) {
    return {};
  }
  return JSON.parse(text) as unknown;
}

function extractApiMessage(status: number, body: unknown): string {
  if (body !== null && typeof body === "object" && "detail" in body) {
    const detail: unknown = (body as { detail: unknown }).detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (Array.isArray(detail)) {
      return JSON.stringify(detail);
    }
  }
  return `Request failed with status ${status}`;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response: Response = await fetchWithNetworkGuard(path, init);
  const text: string = await response.text();
  let body: unknown = {};
  try {
    body = parseJsonBody(text);
  } catch {
    throw new ApiError("Response is not valid JSON", response.status);
  }
  if (!response.ok) {
    throw new ApiError(extractApiMessage(response.status, body), response.status);
  }
  return body as T;
}

export async function getHealth(): Promise<HealthResponse> {
  return fetchJson<HealthResponse>("/health");
}

export interface GetFeedOptions {
  topic?: NewsTopic;
  urgent?: boolean;
  positive_only?: boolean;
  /** Calendar window on server (Europe/Berlin); omit when ``all``. */
  period?: Exclude<FeedPeriodKey, "all">;
  /** Page size (default 30 on server). */
  limit?: number;
  /** Previous page ``next_cursor`` — continue older items. */
  cursor?: number;
}

export interface NewsFeedPageResponse {
  items: NewsFeedItem[];
  next_cursor: number | null;
}

export interface TopNewsTodayResponse {
  items: NewsFeedItem[];
}

export async function getFeed(options?: GetFeedOptions): Promise<NewsFeedPageResponse> {
  const params: URLSearchParams = new URLSearchParams();
  if (options?.urgent) {
    params.set("urgent", "true");
  } else if (options?.positive_only) {
    params.set("positive_only", "true");
  } else if (options?.topic) {
    params.set("topic", options.topic);
  }
  if (options?.period !== undefined) {
    params.set("period", options.period);
  }
  if (options?.limit !== undefined) {
    params.set("limit", String(options.limit));
  }
  if (options?.cursor !== undefined) {
    params.set("cursor", String(options.cursor));
  }
  const q: string = params.toString();
  const raw: unknown = await fetchJson<unknown>(`/news${q ? `?${q}` : ""}`);
  if (Array.isArray(raw)) {
    return { items: raw as NewsFeedItem[], next_cursor: null as number | null };
  }
  return raw as NewsFeedPageResponse;
}

export async function getTopNewsToday(limit: number = 5): Promise<TopNewsTodayResponse> {
  const params: URLSearchParams = new URLSearchParams({ limit: String(limit) });
  return fetchJson<TopNewsTodayResponse>(`/news/top-today?${params.toString()}`);
}

export async function postEngagementBatch(body: EngagementBatchRequestBody): Promise<EngagementBatchResponseBody> {
  return fetchJson<EngagementBatchResponseBody>("/engagement/events", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
}

export async function getNews(newsId: number): Promise<ProcessedNews> {
  return fetchJson<ProcessedNews>(`/news/${newsId}`);
}

export async function getNewsFullArticle(newsId: number): Promise<FullArticleResponse> {
  return fetchJson<FullArticleResponse>(`/news/${newsId}/full-article`);
}

function bearerHeaders(accessToken: string): HeadersInit {
  return { Authorization: `Bearer ${accessToken}` };
}

async function fetchJsonAuthorized<T>(
  path: string,
  accessToken: string,
  init?: Omit<RequestInit, "headers"> & { headers?: HeadersInit },
): Promise<T> {
  const merged: RequestInit = {
    ...init,
    headers: { ...bearerHeaders(accessToken), ...init?.headers },
  };
  return fetchJson<T>(path, merged);
}

export async function authRegister(payload: UserRegisterCredentials): Promise<RegisterResponse> {
  return fetchJson<RegisterResponse>("/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function authVerifyEmail(token: string): Promise<UserTokenPair> {
  return fetchJson<UserTokenPair>("/auth/verify-email", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token }),
  });
}

export async function authResendVerification(email: string): Promise<RegisterResponse> {
  return fetchJson<RegisterResponse>("/auth/resend-verification", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export async function authLogin(payload: UserLoginCredentials): Promise<UserTokenPair> {
  return fetchJson<UserTokenPair>("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function authRefresh(refreshTokenPlain: string): Promise<UserTokenPair> {
  return fetchJson<UserTokenPair>("/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshTokenPlain }),
  });
}

export async function authLogout(refreshTokenPlain: string): Promise<void> {
  await fetchJson<{ detail?: string }>("/auth/logout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshTokenPlain }),
  });
}

export async function authMe(accessToken: string): Promise<UserMe> {
  return fetchJsonAuthorized<UserMe>("/auth/me", accessToken, { method: "GET" });
}

export interface ForgotPasswordResponse {
  detail: string;
  dev_reset_link?: string | null;
}

export async function authForgotPassword(email: string): Promise<ForgotPasswordResponse> {
  return fetchJson<ForgotPasswordResponse>("/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export async function authResetPassword(token: string, newPassword: string): Promise<{ detail: string }> {
  return fetchJson<{ detail: string }>("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function getModerationQueue(accessToken: string): Promise<ProcessedNews[]> {
  return fetchJsonAuthorized<ProcessedNews[]>("/moderation/queue", accessToken, { method: "GET" });
}

export async function moderate(
  newsId: number,
  action: "approve" | "reject",
  accessToken: string,
): Promise<ProcessedNews> {
  return fetchJsonAuthorized<ProcessedNews>(`/moderation/${newsId}/action`, accessToken, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
}

export interface NewsMetadataPatch {
  topic?: NewsTopic;
  is_urgent?: boolean;
  is_positive?: boolean;
}

export async function patchNewsMetadata(
  newsId: number,
  patch: NewsMetadataPatch,
  accessToken: string,
): Promise<ProcessedNews> {
  return fetchJsonAuthorized<ProcessedNews>(`/moderation/${newsId}/metadata`, accessToken, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(patch),
  });
}

export interface PushSubscriptionResponseBody {
  subscribed: boolean;
  topic: string;
}

export async function subscribePush(deviceToken: string): Promise<PushSubscriptionResponseBody> {
  return fetchJson<PushSubscriptionResponseBody>("/push/subscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_token: deviceToken, platform: "android" }),
  });
}

export async function unsubscribePush(deviceToken: string): Promise<PushSubscriptionResponseBody> {
  return fetchJson<PushSubscriptionResponseBody>("/push/unsubscribe", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ device_token: deviceToken }),
  });
}

/**
 * Manual `POST /pipeline/run`. On HTTP 2xx returns typed body (may include `ok: false`
 * when the backend swallows errors; manual run usually raises on failure → 5xx).
 */
export async function runPipeline(accessToken: string): Promise<PipelineRunResponse> {
  const response: Response = await fetchWithNetworkGuard("/pipeline/run", {
    method: "POST",
    headers: { ...bearerHeaders(accessToken) },
  });
  const text: string = await response.text();
  let body: unknown = {};
  try {
    body = parseJsonBody(text);
  } catch {
    throw new ApiError("Response is not valid JSON", response.status);
  }
  if (!response.ok) {
    throw new ApiError(extractApiMessage(response.status, body), response.status);
  }
  return body as PipelineRunResponse;
}
