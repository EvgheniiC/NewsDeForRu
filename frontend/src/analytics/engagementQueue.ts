import { getAnonymousUserId } from "../lib/anonymousUserId";
import { getSessionId } from "../lib/sessionId";
import type { ClientEngagementEvent, EngagementBatchResponseBody, EngagementEventType } from "../types/engagement";
import { ApiError, NetworkError, postEngagementBatch } from "../api/client";

const FLUSH_MS: number = 850;
const MAX_QUEUE: number = 40;

let queue: ClientEngagementEvent[] = [];
let flushTimer: ReturnType<typeof setTimeout> | null = null;
let flushing: boolean = false;

function newClientEventId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `ce-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export function enqueueEngagement(events: ClientEngagementEvent[]): void {
  if (events.length === 0) {
    return;
  }
  for (const e of events) {
    queue.push(e);
  }
  while (queue.length > MAX_QUEUE) {
    queue.shift();
  }
  scheduleFlush();
}

export function enqueueOne(
  newsId: number,
  eventType: EngagementEventType,
  payload: Record<string, unknown>,
  withClientDedupId: boolean
): void {
  enqueueEngagement([
    {
      news_id: newsId,
      event_type: eventType,
      payload,
      client_event_id: withClientDedupId ? newClientEventId() : null
    }
  ]);
}

function scheduleFlush(): void {
  if (flushTimer !== null) {
    return;
  }
  flushTimer = window.setTimeout(() => {
    flushTimer = null;
    void flushEngagementQueue();
  }, FLUSH_MS);
}

export async function flushEngagementQueue(): Promise<void> {
  if (flushing || queue.length === 0) {
    return;
  }
  flushing = true;
  const batch: ClientEngagementEvent[] = queue;
  queue = [];
  try {
    const body: EngagementBatchResponseBody = await postEngagementBatch({
      anonymous_user_id: getAnonymousUserId(),
      session_id: getSessionId(),
      events: batch
    });
    if (body.inserted + body.skipped_duplicate < batch.length) {
      // partial failure unlikely; re-queue if needed in future
    }
  } catch (e: unknown) {
    if (e instanceof NetworkError || (e instanceof ApiError && e.status >= 500)) {
      queue = batch.concat(queue);
    }
  } finally {
    flushing = false;
    if (queue.length > 0) {
      scheduleFlush();
    }
  }
}

export function flushEngagementQueueSyncOnUnload(): void {
  window.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      void flushEngagementQueue();
    }
  });
  window.addEventListener("pagehide", () => {
    void flushEngagementQueue();
  });
}
