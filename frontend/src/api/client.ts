import type { NewsFeedItem, ProcessedNews, RoleImpact } from "../types/news";

const API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export class ApiError extends Error {
  public readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response: Response = await fetch(`${API_BASE_URL}${path}`, init);
  if (!response.ok) {
    throw new ApiError(`Request failed with status ${response.status}`, response.status);
  }
  return (await response.json()) as T;
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

export async function runPipeline(): Promise<void> {
  await fetchJson("/pipeline/run", { method: "POST" });
}
