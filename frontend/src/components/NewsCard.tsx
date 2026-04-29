import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import { enqueueOne } from "../analytics/engagementQueue";
import type { FeedAnalyticsMode } from "../types/engagement";
import type { NewsFeedItem } from "../types/news";

export type NewsCardVariant = "compact" | "immersive";

const USEFUL_STORAGE_PREFIX: string = "nga_useful_";

interface NewsCardProps {
  item: NewsFeedItem;
  variant?: NewsCardVariant;
  /** Used in `navigate_next` payloads from parent feeds; card events include scroll/useful/open. */
  feedMode?: FeedAnalyticsMode;
}

function readStoredUseful(newsId: number): boolean {
  try {
    return window.localStorage.getItem(`${USEFUL_STORAGE_PREFIX}${newsId}`) === "1";
  } catch {
    return false;
  }
}

export function NewsCard({ item, variant = "compact", feedMode = "grid" }: NewsCardProps): JSX.Element {
  const [useful, setUseful] = useState<boolean>(() => readStoredUseful(item.id));
  const readCompleteSentRef: { current: boolean } = useRef<boolean>(false);
  const scrollRootRef: { current: HTMLDivElement | null } = useRef<HTMLDivElement | null>(null);
  const sentinelRef: { current: HTMLDivElement | null } = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setUseful(readStoredUseful(item.id));
  }, [item.id]);

  useEffect(() => {
    readCompleteSentRef.current = false;
  }, [item.id]);

  useEffect(() => {
    const root: HTMLDivElement | null = scrollRootRef.current;
    const sentinel: HTMLDivElement | null = sentinelRef.current;
    if (root === null || sentinel === null) {
      return;
    }
    const observer: IntersectionObserver = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        for (const entry of entries) {
          if (entry.target !== sentinel) {
            continue;
          }
          if (!(entry.isIntersecting && entry.intersectionRatio >= 0.99)) {
            continue;
          }
          if (readCompleteSentRef.current) {
            continue;
          }
          readCompleteSentRef.current = true;
          enqueueOne(item.id, "read_complete_preview", { max_ratio: 1 }, true);
          break;
        }
      },
      { root, rootMargin: "0px", threshold: [0.99] }
    );
    observer.observe(sentinel);
    return (): void => {
      observer.disconnect();
    };
  }, [item.id, variant]);

  const rootClass: string = variant === "immersive" ? "news-card news-card-immersive" : "news-card";
  const scrollClass: string =
    variant === "immersive" ? "news-card-scroll news-card-scroll-immersive" : "news-card-scroll";

  const handleUsefulClick = (): void => {
    const next: boolean = !useful;
    setUseful(next);
    try {
      window.localStorage.setItem(`${USEFUL_STORAGE_PREFIX}${item.id}`, next ? "1" : "0");
    } catch {
      /* storage full or disabled */
    }
    enqueueOne(item.id, "useful", { value: next }, true);
  };

  const handleOpenPreviewClick = (): void => {
    enqueueOne(item.id, "open_preview", { feed_mode: feedMode }, true);
  };

  return (
    <article className={rootClass}>
      {item.is_urgent ? <span className="news-urgent-badge">⚡ Срочно</span> : null}
      <h3>{item.title}</h3>
      {item.image_url ? (
        <img
          alt={item.title}
          className="news-card-image"
          decoding="async"
          loading="lazy"
          src={item.image_url}
        />
      ) : null}
      <div className={scrollClass} ref={scrollRootRef}>
        <p className={variant === "immersive" ? "news-card-subtitle-immersive" : undefined}>{item.subtitle}</p>
        <div aria-hidden="true" className="news-card-read-sentinel" ref={sentinelRef} />
      </div>
      <div className="news-card-footer">
        <span>⏱ {item.read_time_minutes} мин</span>
        <div className="news-card-actions">
          <button
            aria-pressed={useful}
            className={useful ? "news-useful-btn is-active" : "news-useful-btn"}
            onClick={handleUsefulClick}
            type="button"
          >
            ❤️ Полезно
          </button>
          <Link onClick={handleOpenPreviewClick} to={`/news/${item.id}`}>
            Открыть
          </Link>
        </div>
      </div>
    </article>
  );
}
