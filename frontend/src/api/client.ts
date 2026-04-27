import type { NewsFeedItem, ProcessedNews, RoleImpact } from "../types/news";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

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

export async function getFeed(): Promise<NewsFeedItem[]> {
  return fetchJson<NewsFeedItem[]>("/news");
}

export async function getNews(newsId: number): Promise<ProcessedNews> {
  return fetchJson<ProcessedNews>(`/news/${newsId}`);
}

export async function getNewsImpact(newsId: number, role: string): Promise<RoleImpact> {
  return fetchJson<RoleImpact>(`/news/${newsId}/impact?role=${role}`);
}

export async function getModerationQueue(): Promise<ProcessedNews[]> {
  return fetchJson<ProcessedNews[]>("/moderation/queue");
}

export async function moderate(newsId: number, action: "approve" | "reject"): Promise<ProcessedNews> {
  return fetchJson<ProcessedNews>(`/moderation/${newsId}/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action })
  });
}

/**
 * Manual `POST /pipeline/run`. On HTTP 2xx returns typed body (may include `ok: false`
 * when the backend swallows errors; manual run usually raises on failure → 5xx).
 */
export async function runPipeline(): Promise<PipelineRunResponse> {
  const response: Response = await fetchWithNetworkGuard("/pipeline/run", { method: "POST" });
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
