/** Mirrors backend `PipelineRunResponse` (`app/schemas/news.py`). */
export interface PipelineRunResponse {
  fetched: number;
  feeds_failed: number;
  filtered_out: number;
  clustered: number;
  processed: number;
  published: number;
  needs_review: number;
  item_errors: number;
  ok: boolean;
  error: string | null;
}

/** Response shape of `GET /health` (`app/api/routes/health.py`). */
export interface HealthResponse {
  status: "ok" | "degraded";
  database: "ok" | "unavailable";
  last_pipeline_run_at: string | null;
  last_pipeline_ok: boolean | null;
  pipeline_scheduler: "enabled" | "disabled";
}
