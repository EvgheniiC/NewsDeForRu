/** Mirrors backend `EngagementEventType`. */
export type EngagementEventType =
  | "useful"
  | "open_preview"
  | "open_source"
  | "read_complete_preview"
  | "read_complete_article"
  | "navigate_next";

export type FeedAnalyticsMode = "grid" | "tiktok" | "fast";

/** One row sent inside `POST /engagement/events`. */
export interface ClientEngagementEvent {
  news_id: number;
  event_type: EngagementEventType;
  client_event_id: string | null;
  payload: Record<string, unknown>;
}

export interface EngagementBatchRequestBody {
  anonymous_user_id: string;
  session_id: string;
  events: ClientEngagementEvent[];
}

export interface EngagementBatchResponseBody {
  inserted: number;
  skipped_duplicate: number;
}
