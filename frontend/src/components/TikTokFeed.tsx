import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { enqueueOne } from "../analytics/engagementQueue";
import { queueScrollPastNews } from "../lib/scrollToRead";
import { NewsCard } from "./NewsCard";
import { SwipeToReadSnap } from "./SwipeToReadSnap";
import type { NewsFeedItem } from "../types/news";

const QUICK_NAV_MS: number = 2200;
/** Matches CSS phone snap breakpoint in styles.css (`@media (max-width: 640px)`). */
const PHONE_SNAP_MEDIA: string = "(max-width: 640px)";

interface TikTokFeedProps {
  items: NewsFeedItem[];
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  swipeToRead?: boolean;
  scrollToRead?: boolean;
  /** Archive tabs (saved/read): stacked cards instead of fixed-height snap pages. */
  stackedLayout?: boolean;
}

/** Keep the same on-screen card (or its successor) after items are removed from the list. */
function resolveScrollAnchorId(
  prevItems: NewsFeedItem[],
  nextItems: NewsFeedItem[],
  prevScrollTop: number,
  viewportHeight: number
): number | null {
  if (prevItems.length === 0 || nextItems.length === 0 || viewportHeight <= 0) {
    return null;
  }
  const prevIndex: number = Math.min(
    Math.max(Math.round(prevScrollTop / viewportHeight), 0),
    prevItems.length - 1
  );
  const prevVisibleId: number = prevItems[prevIndex].id;
  const nextIds: Set<number> = new Set(nextItems.map((item: NewsFeedItem) => item.id));
  if (nextIds.has(prevVisibleId)) {
    return prevVisibleId;
  }
  const anchor: NewsFeedItem | undefined = nextItems[Math.min(prevIndex, nextItems.length - 1)];
  return anchor?.id ?? null;
}

export function TikTokFeed({
  items,
  hasMore,
  loadingMore,
  onLoadMore,
  swipeToRead = false,
  scrollToRead = false,
  stackedLayout = false
}: TikTokFeedProps): JSX.Element {
  const scrollRootRef = useRef<HTMLDivElement | null>(null);
  const sentinelRef = useRef<HTMLDivElement | null>(null);
  const prevItemsRef = useRef<NewsFeedItem[]>(items);
  const scrollTopRef = useRef<number>(0);
  const [phoneSnapViewport, setPhoneSnapViewport] = useState<boolean>(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return false;
    }
    return window.matchMedia(PHONE_SNAP_MEDIA).matches;
  });

  useEffect(() => {
    if (typeof window.matchMedia !== "function") {
      return;
    }
    const media: MediaQueryList = window.matchMedia(PHONE_SNAP_MEDIA);
    const onChange = (): void => {
      setPhoneSnapViewport(media.matches);
    };
    onChange();
    media.addEventListener("change", onChange);
    return (): void => {
      media.removeEventListener("change", onChange);
    };
  }, []);

  /** Desktop list + archive stacked tabs: expand in card. Phone snap keeps «Открыть». */
  const expandInPlace: boolean = stackedLayout || !phoneSnapViewport;
  const cardFeedMode: "grid" | "tiktok" = expandInPlace ? "grid" : "tiktok";

  useEffect(() => {
    const root: HTMLDivElement | null = scrollRootRef.current;
    if (root === null) {
      return;
    }
    const onScroll = (): void => {
      scrollTopRef.current = root.scrollTop;
    };
    onScroll();
    root.addEventListener("scroll", onScroll, { passive: true });
    return (): void => {
      root.removeEventListener("scroll", onScroll);
    };
  }, []);

  useLayoutEffect(() => {
    const root: HTMLDivElement | null = scrollRootRef.current;
    const prevItems: NewsFeedItem[] = prevItemsRef.current;
    prevItemsRef.current = items;
    if (root === null || stackedLayout || prevItems.length === 0) {
      return;
    }
    const nextIds: Set<number> = new Set(items.map((item: NewsFeedItem) => item.id));
    const somethingRemoved: boolean = prevItems.some((item: NewsFeedItem) => !nextIds.has(item.id));
    if (!somethingRemoved) {
      return;
    }
    const anchorId: number | null = resolveScrollAnchorId(
      prevItems,
      items,
      scrollTopRef.current,
      root.clientHeight
    );
    if (anchorId === null) {
      return;
    }
    const el: Element | null = root.querySelector(`.tiktok-feed-snap[data-news-id="${String(anchorId)}"]`);
    if (el instanceof HTMLElement) {
      el.scrollIntoView({ block: "start", behavior: "instant" });
      scrollTopRef.current = root.scrollTop;
    }
  }, [items, stackedLayout]);

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
          if (scrollToRead) {
            queueScrollPastNews(activeId);
          }
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
  }, [items, scrollToRead]);

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

  const feedClassName: string = stackedLayout ? "tiktok-feed tiktok-feed--stacked" : "tiktok-feed";

  return (
    <div className={feedClassName} aria-label="Вертикальная лента">
      <div className="tiktok-feed-scroll" ref={scrollRootRef}>
        {items.map((item: NewsFeedItem) => {
          const card: JSX.Element = (
            <NewsCard
              expandInPlace={expandInPlace}
              feedMode={cardFeedMode}
              item={item}
              variant="immersive"
            />
          );
          const snap: JSX.Element = (
            <div className="tiktok-feed-snap" data-news-id={String(item.id)} key={item.id}>
              {card}
            </div>
          );
          if (!swipeToRead) {
            return snap;
          }
          return (
            <SwipeToReadSnap className="tiktok-feed-snap" dataNewsId={String(item.id)} item={item} key={item.id}>
              {card}
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
