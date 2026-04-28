import { useEffect, useRef } from "react";
import { NewsCard } from "./NewsCard";
import type { NewsFeedItem } from "../types/news";

interface TikTokFeedProps {
  items: NewsFeedItem[];
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
}

export function TikTokFeed({ items, hasMore, loadingMore, onLoadMore }: TikTokFeedProps): JSX.Element {
  const sentinelRef = useRef<HTMLDivElement | null>(null);

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
      <div className="tiktok-feed-scroll">
        {items.map((item: NewsFeedItem) => (
          <div className="tiktok-feed-snap" key={item.id}>
            <NewsCard item={item} variant="immersive" />
          </div>
        ))}
        {hasMore ? (
          <div className="tiktok-feed-snap tiktok-feed-sentinel" ref={sentinelRef} aria-hidden="true">
            {loadingMore ? <p className="muted tiktok-feed-loading">Загрузка…</p> : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
