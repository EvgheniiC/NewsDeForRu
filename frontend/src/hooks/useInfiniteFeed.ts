import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, getFeed, getTopNewsToday, NetworkError, type GetFeedOptions } from "../api/client";
import type { FeedFilterKey, FeedPeriodKey, NewsFeedItem } from "../types/news";

const PAGE_SIZE: number = 20;

function buildFeedRequestOptions(
  feedFilter: Exclude<FeedFilterKey, "top_today" | "saved_useful">,
  period: FeedPeriodKey
): Omit<GetFeedOptions, "cursor"> {
  const base: Omit<GetFeedOptions, "cursor"> =
    feedFilter === "urgent"
      ? { urgent: true, limit: PAGE_SIZE }
      : feedFilter === "positive"
        ? { positive_only: true, limit: PAGE_SIZE }
        : { topic: feedFilter, limit: PAGE_SIZE };
  if (period === "all") {
    return base;
  }
  return { ...base, period };
}

async function loadFeedFirstPage(
  feedFilter: Exclude<FeedFilterKey, "saved_useful">,
  period: FeedPeriodKey
): Promise<{ items: NewsFeedItem[]; next_cursor: number | null }> {
  if (feedFilter === "top_today") {
    const top = await getTopNewsToday(5);
    return { items: top.items, next_cursor: null };
  }
  const response = await getFeed(buildFeedRequestOptions(feedFilter, period));
  return normalizeFeedItems(response as { items?: unknown; next_cursor?: unknown });
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

export interface UseInfiniteFeedOptions {
  /** When false, no fetches run (for alternate tabs like saved useful). */
  enabled?: boolean;
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

type StandardFeedFilter = Exclude<FeedFilterKey, "saved_useful">;

export function useInfiniteFeed(
  feedFilter: StandardFeedFilter,
  period: FeedPeriodKey,
  options: UseInfiniteFeedOptions = {}
): UseInfiniteFeedResult {
  const enabled: boolean = options.enabled !== false;
  const [items, setItems] = useState<NewsFeedItem[]>([]);
  const [nextCursor, setNextCursor] = useState<number | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [feedError, setFeedError] = useState<string>("");

  const feedFilterRef: { current: StandardFeedFilter } = useRef<StandardFeedFilter>(feedFilter);
  const periodRef: { current: FeedPeriodKey } = useRef<FeedPeriodKey>(period);
  const enabledRef: { current: boolean } = useRef<boolean>(enabled);

  useEffect(() => {
    feedFilterRef.current = feedFilter;
    periodRef.current = period;
    enabledRef.current = enabled;
  }, [feedFilter, period, enabled]);

  const fetchGenRef: { current: number } = useRef<number>(0);
  const loadMoreSeqRef: { current: number } = useRef<number>(0);

  useEffect(() => {
    if (!enabled) {
      setItems([]);
      setNextCursor(null);
      setFeedError("");
      setLoading(false);
      return;
    }
    loadMoreSeqRef.current += 1;
    fetchGenRef.current += 1;
    const fetchId: number = fetchGenRef.current;

    setItems([]);
    setNextCursor(null);
    setFeedError("");
    setLoading(true);

    void (async (): Promise<void> => {
      try {
        const normalized = await loadFeedFirstPage(feedFilter, period);
        if (fetchId !== fetchGenRef.current) {
          return;
        }
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
  }, [feedFilter, period, enabled]);

  const reload = useCallback(async (): Promise<void> => {
    if (!enabledRef.current) {
      return;
    }
    fetchGenRef.current += 1;
    const fetchId: number = fetchGenRef.current;
    const snapshotFilter: StandardFeedFilter = feedFilterRef.current;
    const snapshotPeriod: FeedPeriodKey = periodRef.current;

    setFeedError("");
    setLoading(true);
    try {
      const normalized = await loadFeedFirstPage(snapshotFilter, snapshotPeriod);
      if (fetchId !== fetchGenRef.current) {
        return;
      }
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
    if (!enabledRef.current || feedFilter === "top_today" || nextCursor === null || loadingMore) {
      return;
    }
    loadMoreSeqRef.current += 1;
    const seq: number = loadMoreSeqRef.current;
    setLoadingMore(true);
    try {
      const options: GetFeedOptions = {
        ...buildFeedRequestOptions(feedFilter, period),
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
