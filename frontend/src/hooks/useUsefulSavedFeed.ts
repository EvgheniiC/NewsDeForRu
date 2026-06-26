import { useCallback, useEffect, useState } from "react";
import { ApiError, getNews, NetworkError } from "../api/client";
import {
  USEFUL_STATE_STORAGE_KEY,
  USEFUL_STORAGE_CHANGED_EVENT,
  USEFUL_STORAGE_PREFIX,
  listUsefulMarkedNewsIds
} from "../lib/usefulStorage";
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
  return "Не удалось загрузить сохранённые новости.";
}

export interface UseUsefulSavedFeedResult {
  items: NewsFeedItem[];
  loading: boolean;
  feedError: string;
  refresh: () => Promise<void>;
}

export function useUsefulSavedFeed(enabled: boolean): UseUsefulSavedFeedResult {
  const [items, setItems] = useState<NewsFeedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [feedError, setFeedError] = useState<string>("");

  const load = useCallback(async (): Promise<void> => {
    if (!enabled) {
      return;
    }
    setLoading(true);
    setFeedError("");
    const ids: number[] = listUsefulMarkedNewsIds();
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
      out.sort((a: NewsFeedItem, b: NewsFeedItem) => (a.created_at < b.created_at ? 1 : -1));
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
      if (e.key === USEFUL_STATE_STORAGE_KEY || (e.key !== null && e.key.startsWith(USEFUL_STORAGE_PREFIX))) {
        void load();
      }
    };
    const onCustom = (): void => {
      void load();
    };
    window.addEventListener("storage", onStorage);
    window.addEventListener(USEFUL_STORAGE_CHANGED_EVENT, onCustom);
    return (): void => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(USEFUL_STORAGE_CHANGED_EVENT, onCustom);
    };
  }, [enabled, load]);

  return { items, loading, feedError, refresh: load };
}
