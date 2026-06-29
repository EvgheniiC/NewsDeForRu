import { useEffect, useRef } from "react";
import { enqueueOne } from "../analytics/engagementQueue";
import { NewsCard } from "./NewsCard";
import { SwipeToReadSnap } from "./SwipeToReadSnap";
import type { NewsFeedItem } from "../types/news";

const QUICK_NAV_MS: number = 2200;
const SNAP_IDLE_MS: number = 280;
const SNAP_MIN_OFFSET_PX: number = 8;

function snapFeedToNearestCard(root: HTMLDivElement): void {
  const snaps: NodeListOf<HTMLElement> = root.querySelectorAll(".tiktok-feed-snap[data-news-id]");
  if (snaps.length === 0) {
    return;
  }

  const rootRect: DOMRect = root.getBoundingClientRect();
  const snapAnchorY: number = rootRect.top;

  let bestElement: HTMLElement | null = null;
  let bestDistance: number = Number.POSITIVE_INFINITY;

  snaps.forEach((element: HTMLElement) => {
    const rect: DOMRect = element.getBoundingClientRect();
    const distance: number = Math.abs(rect.top - snapAnchorY);
    if (distance < bestDistance) {
      bestDistance = distance;
      bestElement = element;
    }
  });

  if (bestElement !== null && bestDistance > SNAP_MIN_OFFSET_PX) {
    bestElement.scrollIntoView({ behavior: "instant", block: "start" });
  }
}

interface TikTokFeedProps {
  items: NewsFeedItem[];
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  swipeToRead?: boolean;
}

export function TikTokFeed({
  items,
  hasMore,
  loadingMore,
  onLoadMore,
  swipeToRead = false
}: TikTokFeedProps): JSX.Element {
  const scrollRootRef = useRef<HTMLDivElement | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const snapTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const root: HTMLDivElement | null = scrollRootRef.current;
    if (root === null) {
      return;
    }

    const scheduleSnap = (): void => {
      if (snapTimerRef.current !== null) {
        window.clearTimeout(snapTimerRef.current);
      }
      snapTimerRef.current = window.setTimeout(() => {
        snapTimerRef.current = null;
        snapFeedToNearestCard(root);
      }, SNAP_IDLE_MS);
    };

    const onScrollEnd = (): void => {
      snapFeedToNearestCard(root);
    };

    root.addEventListener("scroll", scheduleSnap, { passive: true });
    root.addEventListener("scrollend", onScrollEnd);

    return (): void => {
      root.removeEventListener("scroll", scheduleSnap);
      root.removeEventListener("scrollend", onScrollEnd);
      if (snapTimerRef.current !== null) {
        window.clearTimeout(snapTimerRef.current);
        snapTimerRef.current = null;
      }
    };
  }, [items.length]);

  useEffect(() => {
    const root: HTMLDivElement | null = scrollRootRef.current;
    if (root === null || items.length === 0) {
      return;
    }

    const ratios: Map<number, number> = new Map();
    let activeId: number | null = null;
    let activeSinceMs: number = Date.now();

    const observer: IntersectionObserver = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        for (const entry of entries) {
          const el: HTMLElement | null =
            entry.target instanceof HTMLElement ? entry.target : null;
          if (el === null || el.dataset.newsId === undefined) {
            continue;
          }
          const id: number = Number(el.dataset.newsId);
          if (!Number.isFinite(id)) {
            continue;
          }
          ratios.set(id, entry.intersectionRatio);
        }

        const allowedIds: Set<number> = new Set(items.map((i: NewsFeedItem) => i.id));
        for (const id of ratios.keys()) {
          if (!allowedIds.has(id)) {
            ratios.delete(id);
          }
        }

        let bestId: number | null = null;
        let bestRatio: number = 0;
        for (const [id, r] of ratios.entries()) {
          if (r > bestRatio) {
            bestRatio = r;
            bestId = id;
          }
        }
        if (bestId === null || bestRatio < 0.42) {
          return;
        }
        if (activeId === null) {
          activeId = bestId;
          activeSinceMs = Date.now();
          return;
        }
        if (activeId !== bestId) {
          const dwellMs: number = Math.max(0, Date.now() - activeSinceMs);
          const quick: boolean = dwellMs < QUICK_NAV_MS;
          enqueueOne(activeId, "navigate_next", { dwell_ms: dwellMs, quick, feed_mode: "tiktok" }, true);
          activeId = bestId;
          activeSinceMs = Date.now();
        }
      },
      { root, rootMargin: "0px", threshold: [0, 0.05, 0.1, 0.25, 0.5, 0.75, 1.0] }
    );

    const nodes: NodeListOf<HTMLElement> = root.querySelectorAll(".tiktok-feed-snap[data-news-id]");
    nodes.forEach((el: HTMLElement) => {
      observer.observe(el);
    });

    return (): void => {
      nodes.forEach((el: HTMLElement) => {
        observer.unobserve(el);
      });
      observer.disconnect();
    };
  }, [items]);

  useEffect(() => {
    const el: HTMLDivElement | null = sentinelRef.current;
    if (el === null) {
      return;
    }
    const observer: IntersectionObserver = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        if (entries[0]?.isIntersecting && hasMore && !loadingMore) {
          onLoadMore();
        }
      },
      { root: null, rootMargin: "120px", threshold: 0 }
    );
    observer.observe(el);
    return (): void => {
      observer.disconnect();
    };
  }, [hasMore, loadingMore, onLoadMore, items.length]);

  return (
    <div className="tiktok-feed" aria-label="Вертикальная лента">
      <div className="tiktok-feed-scroll" ref={scrollRootRef}>
        {items.map((item: NewsFeedItem) => {
          const snap: JSX.Element = (
            <div className="tiktok-feed-snap" data-news-id={String(item.id)} key={item.id}>
              <NewsCard feedMode="tiktok" item={item} variant="immersive" />
            </div>
          );
          if (!swipeToRead) {
            return snap;
          }
          return (
            <SwipeToReadSnap className="tiktok-feed-snap" dataNewsId={String(item.id)} item={item} key={item.id}>
              <NewsCard feedMode="tiktok" item={item} variant="immersive" />
            </SwipeToReadSnap>
          );
        })}
        {hasMore ? (
          <div className="tiktok-feed-snap tiktok-feed-sentinel" ref={sentinelRef} aria-hidden="true">
            {loadingMore ? <p className="muted tiktok-feed-loading">Загрузка…</p> : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
