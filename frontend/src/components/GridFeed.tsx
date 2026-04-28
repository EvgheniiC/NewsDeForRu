import { useEffect, useRef } from "react";
import { NewsCard } from "./NewsCard";
import type { NewsFeedItem } from "../types/news";

interface GridFeedProps {
  items: NewsFeedItem[];
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
  feedLoading: boolean;
}

export function GridFeed({ items, hasMore, loadingMore, onLoadMore, feedLoading }: GridFeedProps): JSX.Element {
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
      { root: null, rootMargin: "240px", threshold: 0 }
    );
    observer.observe(el);
    return (): void => {
      observer.disconnect();
    };
  }, [hasMore, loadingMore, onLoadMore, items.length]);

  return (
    <>
      <div className={`news-grid ${feedLoading ? "news-grid-dim" : ""}`}>
        {items.map((item: NewsFeedItem) => (
          <NewsCard feedMode="grid" item={item} key={item.id} />
        ))}
      </div>
      {hasMore ? <div className="feed-grid-sentinel" ref={sentinelRef} aria-hidden="true" /> : null}
      {loadingMore && hasMore ? <p className="loading-inline">Подгрузка ленты…</p> : null}
    </>
  );
}
