import { useCallback, useEffect, useState } from "react";
import { ApiError, getNews, NetworkError } from "../api/client";
import {
  listReadNewsIds,
  READ_STATE_CHANGED_EVENT,
  READ_STATE_STORAGE_KEY
} from "../lib/readStateStorage";
import { processedNewsToFeedItem, type NewsFeedItem } from "../types/news";

function feedErrorMessage(e: unknown): string {
  if (e instanceof NetworkError) {
    return `Сеть: ${e.message}`;
  }
  if (e instanceof ApiError) {
    return `Сервер (${e.status}): ${e.message}`;
  }
  if (e instanceof Error) {
    return e.message;
  }
  return "Не удалось загрузить прочитанные новости.";
}

export interface UseReadSavedFeedResult {
  items: NewsFeedItem[];
  loading: boolean;
  feedError: string;
  refresh: () => Promise<void>;
}

export function useReadSavedFeed(enabled: boolean): UseReadSavedFeedResult {
  const [items, setItems] = useState<NewsFeedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [feedError, setFeedError] = useState<string>("");

  const load = useCallback(async (): Promise<void> => {
    if (!enabled) {
      return;
    }
    setLoading(true);
    setFeedError("");
    const ids: number[] = listReadNewsIds();
    if (ids.length === 0) {
      setItems([]);
      setLoading(false);
      return;
    }
    try {
      const settled: PromiseSettledResult<Awaited<ReturnType<typeof getNews>>>[] = await Promise.allSettled(
        ids.map((id: number) => getNews(id))
      );
      const out: NewsFeedItem[] = [];
      for (const r of settled) {
        if (r.status === "fulfilled") {
          out.push(processedNewsToFeedItem(r.value));
        }
      }
      const order: Map<number, number> = new Map(ids.map((id: number, index: number) => [id, index]));
      out.sort((a: NewsFeedItem, b: NewsFeedItem) => (order.get(a.id) ?? 0) - (order.get(b.id) ?? 0));
      setItems(out);
    } catch (e: unknown) {
      setFeedError(feedErrorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [enabled]);

  useEffect(() => {
    if (!enabled) {
      setItems([]);
      setFeedError("");
      setLoading(false);
      return;
    }
    void load();
  }, [enabled, load]);

  useEffect(() => {
    if (!enabled) {
      return;
    }
    const onStorage = (e: StorageEvent): void => {
      if (e.key === READ_STATE_STORAGE_KEY) {
        void load();
      }
    };
    const onCustom = (): void => {
      void load();
    };
    window.addEventListener("storage", onStorage);
    window.addEventListener(READ_STATE_CHANGED_EVENT, onCustom);
    return (): void => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(READ_STATE_CHANGED_EVENT, onCustom);
    };
  }, [enabled, load]);

  return { items, loading, feedError, refresh: load };
}
