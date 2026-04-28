import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getFeed, NetworkError, type GetFeedOptions } from "../api/client";
import type { FeedFilterKey, FeedPeriodKey, NewsFeedItem } from "../types/news";

const PAGE_SIZE: number = 20;

function buildFeedRequestOptions(
  feedFilter: FeedFilterKey,
  period: FeedPeriodKey
): Omit<GetFeedOptions, "cursor"> {
  const base: Omit<GetFeedOptions, "cursor"> =
    feedFilter === "urgent"
      ? { urgent: true, limit: PAGE_SIZE }
      : { topic: feedFilter, limit: PAGE_SIZE };
  if (period === "all") {
    return base;
  }
  return { ...base, period };
}

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
  return "Не удалось загрузить ленту.";
}

/** Only the latest GET /news request updates UI (fixes React Strict Mode + overlapping fetches). */
function normalizeFeedItems(response: { items?: unknown; next_cursor?: unknown }): {
  items: NewsFeedItem[];
  next_cursor: number | null;
} {
  const items: unknown = response.items;
  const rawList: unknown[] = Array.isArray(items) ? items : [];
  const list: NewsFeedItem[] = rawList as NewsFeedItem[];

  let nextCursor: number | null = null;
  const nc: unknown = response.next_cursor;
  if (nc === null || nc === undefined) {
    nextCursor = null;
  } else if (typeof nc === "number") {
    nextCursor = nc;
  }

  return { items: list, next_cursor: nextCursor };
}

export interface UseInfiniteFeedResult {
  items: NewsFeedItem[];
  loading: boolean;
  loadingMore: boolean;
  feedError: string;
  nextCursor: number | null;
  reload: () => Promise<void>;
  loadMore: () => Promise<void>;
}

export function useInfiniteFeed(feedFilter: FeedFilterKey, period: FeedPeriodKey): UseInfiniteFeedResult {
  const [items, setItems] = useState<NewsFeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [feedError, setFeedError] = useState<string>("");

  const feedFilterRef: { current: FeedFilterKey } = useRef<FeedFilterKey>(feedFilter);
  feedFilterRef.current = feedFilter;

  const fetchGenRef: { current: number } = useRef<number>(0);
  const loadMoreSeqRef: { current: number } = useRef<number>(0);

  useEffect(() => {
    loadMoreSeqRef.current += 1;
    fetchGenRef.current += 1;
    const fetchId: number = fetchGenRef.current;

    setItems([]);
    setNextCursor(null);
    setFeedError("");
    setLoading(true);

    void (async (): Promise<void> => {
      try {
        const response = await getFeed(buildFeedRequestOptions(feedFilter, period));
        if (fetchId !== fetchGenRef.current) {
          return;
        }
        const normalized = normalizeFeedItems(response as { items?: unknown; next_cursor?: unknown });
        setItems(normalized.items);
        setNextCursor(normalized.next_cursor);
      } catch (e: unknown) {
        if (fetchId !== fetchGenRef.current) {
          return;
        }
        setFeedError(feedErrorMessage(e));
      } finally {
        if (fetchId === fetchGenRef.current) {
          setLoading(false);
        }
      }
    })();
  }, [feedFilter, period]);

  const reload = useCallback(async (): Promise<void> => {
    fetchGenRef.current += 1;
    const fetchId: number = fetchGenRef.current;
    const snapshotFilter: FeedFilterKey = feedFilterRef.current;
    const snapshotPeriod: FeedPeriodKey = periodRef.current;

    setFeedError("");
    setLoading(true);
    try {
      const response = await getFeed(buildFeedRequestOptions(snapshotFilter, snapshotPeriod));
      if (fetchId !== fetchGenRef.current) {
        return;
      }
      const normalized = normalizeFeedItems(response as { items?: unknown; next_cursor?: unknown });
      setItems(normalized.items);
      setNextCursor(normalized.next_cursor);
    } catch (e: unknown) {
      if (fetchId !== fetchGenRef.current) {
        return;
      }
      setFeedError(feedErrorMessage(e));
    } finally {
      if (fetchId === fetchGenRef.current) {
        setLoading(false);
      }
    }
  }, []);

  const loadMore = useCallback(async (): Promise<void> => {
    if (nextCursor === null || loadingMore) {
      return;
    }
    loadMoreSeqRef.current += 1;
    const seq: number = loadMoreSeqRef.current;
    setLoadingMore(true);
    try {
      const options: GetFeedOptions = {
        ...buildFeedRequestOptions(feedFilter),
        cursor: nextCursor
      };
      const response = await getFeed(options);
      if (seq !== loadMoreSeqRef.current) {
        return;
      }
      const normalized = normalizeFeedItems(response as { items?: unknown; next_cursor?: unknown });
      setItems((prev: NewsFeedItem[]) => [...prev, ...normalized.items]);
      setNextCursor(normalized.next_cursor);
    } catch (e: unknown) {
      if (seq !== loadMoreSeqRef.current) {
        return;
      }
      setFeedError(feedErrorMessage(e));
    } finally {
      setLoadingMore(false);
    }
  }, [feedFilter, period, nextCursor, loadingMore]);

  return {
    items,
    loading,
    loadingMore,
    feedError,
    nextCursor,
    reload,
    loadMore
  };
}
