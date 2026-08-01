import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { enqueueOne } from "../analytics/engagementQueue";
import { ApiError, getNews } from "../api/client";
import { newsCardClassName, newsTopicChipClass } from "../lib/newsUi";
import { formatDateRuBerlin } from "../lib/dateTimeBerlin";
import { readStoredUseful, setStoredUseful } from "../lib/usefulStorage";
import type { FeedAnalyticsMode } from "../types/engagement";
import { newsTopicLabelRu, type NewsFeedItem, type ProcessedNews } from "../types/news";
import { NewsArticleBody } from "./NewsArticleBody";
import { NewsTopicCover } from "./NewsTopicCover";

export type NewsCardVariant = "compact" | "immersive";

interface NewsCardProps {
  item: NewsFeedItem;
  variant?: NewsCardVariant;
  /** Used in `navigate_next` payloads from parent feeds; card events include scroll/useful/open. */
  feedMode?: FeedAnalyticsMode;
}

/** Prefer the snap page wrapper so TikTok feed scroll restoration lands on the full card. */
function resolveScrollTarget(article: HTMLElement): HTMLElement {
  const snap: HTMLElement | null = article.closest(".tiktok-feed-snap");
  return snap ?? article;
}

export function NewsCard({
  item,
  variant = "compact",
  feedMode = "grid"
}: NewsCardProps): JSX.Element {
  const [useful, setUseful] = useState<boolean>(() => readStoredUseful(item.id));
  const [expanded, setExpanded] = useState<boolean>(false);
  const [details, setDetails] = useState<ProcessedNews | null>(null);
  const [detailsLoading, setDetailsLoading] = useState<boolean>(false);
  const [detailsError, setDetailsError] = useState<string>("");
  const readCompleteSentRef: { current: boolean } = useRef<boolean>(false);
  const articleRef: { current: HTMLElement | null } = useRef<HTMLElement | null>(null);
  const scrollRootRef: { current: HTMLDivElement | null } = useRef<HTMLDivElement | null>(null);
  const sentinelRef: { current: HTMLDivElement | null } = useRef<HTMLDivElement | null>(null);
  const expandRequestIdRef: { current: number } = useRef<number>(0);
  /** Set only on user collapse so item-id resets do not steal scroll. */
  const pendingCollapseScrollRef: { current: boolean } = useRef<boolean>(false);

  useEffect(() => {
    setUseful(readStoredUseful(item.id));
  }, [item.id]);

  useEffect(() => {
    readCompleteSentRef.current = false;
    pendingCollapseScrollRef.current = false;
    setExpanded(false);
    setDetails(null);
    setDetailsError("");
    setDetailsLoading(false);
    expandRequestIdRef.current += 1;
  }, [item.id]);

  /** Bring the card to the top of the feed when expanding so reading starts from the title. */
  useEffect(() => {
    if (!expanded) {
      return;
    }
    const el: HTMLElement | null = articleRef.current;
    if (el === null) {
      return;
    }
    window.requestAnimationFrame(() => {
      resolveScrollTarget(el).scrollIntoView({ block: "start", behavior: "smooth" });
    });
  }, [expanded]);

  /**
   * After collapse the card shrinks and scrollTop stays put, so the viewport jumps to a later item.
   * Re-anchor to this card (centered) before paint.
   */
  useLayoutEffect(() => {
    if (expanded || !pendingCollapseScrollRef.current) {
      return;
    }
    pendingCollapseScrollRef.current = false;
    const el: HTMLElement | null = articleRef.current;
    if (el === null) {
      return;
    }
    resolveScrollTarget(el).scrollIntoView({ block: "center", behavior: "instant" });
  }, [expanded]);

  const isTikTokImmersive: boolean = feedMode === "tiktok" && variant === "immersive";

  useEffect(() => {
    const sentinel: HTMLDivElement | null = sentinelRef.current;
    if (sentinel === null || expanded) {
      return;
    }
    const root: Element | null = isTikTokImmersive ? null : scrollRootRef.current;
    if (!isTikTokImmersive && root === null) {
      return;
    }
    const minRatio: number = isTikTokImmersive ? 0.55 : 0.99;
    const observer: IntersectionObserver = new IntersectionObserver(
      (entries: IntersectionObserverEntry[]) => {
        for (const entry of entries) {
          if (entry.target !== sentinel) {
            continue;
          }
          if (!(entry.isIntersecting && entry.intersectionRatio >= minRatio)) {
            continue;
          }
          if (readCompleteSentRef.current) {
            continue;
          }
          readCompleteSentRef.current = true;
          enqueueOne(item.id, "read_complete_preview", { max_ratio: entry.intersectionRatio }, true);
          break;
        }
      },
      { root, rootMargin: "0px", threshold: isTikTokImmersive ? [0, 0.25, 0.55, 0.75, 1] : [0.99] }
    );
    observer.observe(sentinel);
    return (): void => {
      observer.disconnect();
    };
  }, [item.id, variant, feedMode, isTikTokImmersive, expanded]);

  const rootClass: string = newsCardClassName(item, variant);
  const scrollClass: string = isTikTokImmersive
    ? "news-card-body-immersive"
    : variant === "immersive"
      ? "news-card-scroll news-card-scroll-immersive"
      : "news-card-scroll";

  const hasBadges: boolean = item.is_urgent || item.is_positive;

  const handleUsefulClick = (): void => {
    const next: boolean = !useful;
    setUseful(next);
    setStoredUseful(item.id, next);
    enqueueOne(item.id, "useful", { value: next }, true);
  };

  const handleExpandToggle = (): void => {
    if (expanded) {
      expandRequestIdRef.current += 1;
      pendingCollapseScrollRef.current = true;
      setExpanded(false);
      setDetailsError("");
      setDetailsLoading(false);
      return;
    }

    enqueueOne(item.id, "open_preview", { feed_mode: feedMode, expand_in_place: true }, true);
    setExpanded(true);

    if (details !== null) {
      return;
    }

    const requestId: number = expandRequestIdRef.current + 1;
    expandRequestIdRef.current = requestId;
    setDetailsLoading(true);
    setDetailsError("");
    void getNews(item.id)
      .then((data: ProcessedNews) => {
        if (expandRequestIdRef.current !== requestId) {
          return;
        }
        setDetails(data);
      })
      .catch((error: unknown) => {
        if (expandRequestIdRef.current !== requestId) {
          return;
        }
        if (error instanceof ApiError) {
          setDetailsError(error.message);
        } else {
          setDetailsError(error instanceof Error ? error.message : "Не удалось загрузить новость.");
        }
      })
      .finally(() => {
        if (expandRequestIdRef.current === requestId) {
          setDetailsLoading(false);
        }
      });
  };

  return (
    <article className={expanded ? `${rootClass} news-card--expanded` : rootClass} ref={articleRef}>
      {hasBadges ? (
        <div className="news-card-badges">
          {item.is_urgent ? <span className="news-badge news-badge--urgent">Срочно</span> : null}
          {item.is_positive ? <span className="news-badge news-badge--positive">Хорошая новость</span> : null}
        </div>
      ) : null}
      <p className="news-card-meta">
        <span>{formatDateRuBerlin(item.published_at)}</span>
        <span aria-hidden="true"> · </span>
        <span>{item.source_name}</span>
      </p>
      <h3>{item.title}</h3>
      <NewsTopicCover newsId={item.id} topic={item.topic} variant="card" />
      {expanded ? (
        <div className="news-card-expanded-body">
          {detailsLoading ? <p className="muted">Загрузка…</p> : null}
          {detailsError !== "" ? <p className="error">{detailsError}</p> : null}
          {details !== null ? <NewsArticleBody news={details} /> : null}
        </div>
      ) : (
        <div className={scrollClass} ref={scrollRootRef}>
          <p className={variant === "immersive" ? "news-card-subtitle-immersive" : undefined}>
            {item.subtitle}
          </p>
          <div aria-hidden="true" className="news-card-read-sentinel" ref={sentinelRef} />
        </div>
      )}
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
          <button
            aria-expanded={expanded}
            className="news-open-link"
            onClick={handleExpandToggle}
            type="button"
          >
            {expanded ? "Свернуть" : "Раскрыть"}
          </button>
        </div>
      </div>
      <div className="news-card-topic-row">
        <span className={newsTopicChipClass(item.topic)}>{newsTopicLabelRu(item.topic)}</span>
      </div>
    </article>
  );
}
