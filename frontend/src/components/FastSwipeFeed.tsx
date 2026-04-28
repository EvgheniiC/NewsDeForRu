import { useCallback, useEffect, useRef, useState } from "react";
import { enqueueOne } from "../analytics/engagementQueue";
import { NewsCard } from "./NewsCard";
import type { NewsFeedItem } from "../types/news";

const SWIPE_PX: number = 56;
const QUICK_NAV_MS: number = 2200;

interface FastSwipeFeedProps {
  items: NewsFeedItem[];
  hasMore: boolean;
  loadingMore: boolean;
  onLoadMore: () => void;
}

export function FastSwipeFeed({ items, hasMore, loadingMore, onLoadMore }: FastSwipeFeedProps): JSX.Element {
  const [activeIndex, setActiveIndex] = useState<number>(0);
  const [dragPx, setDragPx] = useState<number>(0);
  const touchStartXRef: { current: number | null } = useRef<number | null>(null);

  const count: number = items.length;
  useEffect(() => {
    if (activeIndex > 0 && activeIndex >= count) {
      setActiveIndex(Math.max(0, count - 1));
    }
  }, [activeIndex, count]);

  useEffect(() => {
    if (count > 0 && activeIndex >= count - 2 && hasMore && !loadingMore) {
      onLoadMore();
    }
  }, [activeIndex, count, hasMore, loadingMore, onLoadMore]);

  const emitNavigateFromIndex = useCallback(
    (indexLeaving: number, directionNext: boolean): void => {
      if (indexLeaving < 0 || indexLeaving >= items.length) {
        return;
      }
      const item: NewsFeedItem | undefined = items[indexLeaving];
      if (item === undefined) {
        return;
      }
      const dwellMs: number = Math.max(0, Date.now() - visibleSinceMsRef.current);
      const quick: boolean = directionNext && dwellMs < QUICK_NAV_MS;
      enqueueOne(
        item.id,
        "navigate_next",
        { dwell_ms: dwellMs, quick, feed_mode: "fast", direction: directionNext ? "next" : "prev" },
        true
      );
    },
    [items]
  );

  const goNext = useCallback((): void => {
    setActiveIndex((i: number) => {
      if (i < count - 1) {
        emitNavigateFromIndex(i, true);
        return i + 1;
      }
      if (hasMore && !loadingMore) {
        void onLoadMore();
      }
      return i;
    });
  }, [count, emitNavigateFromIndex, hasMore, loadingMore, onLoadMore]);

  const goPrev = useCallback((): void => {
    setActiveIndex((i: number) => {
      if (i > 0) {
        emitNavigateFromIndex(i, false);
        return i - 1;
      }
      return 0;
    });
  }, [emitNavigateFromIndex]);

  const onTouchStart = (e: React.TouchEvent<HTMLDivElement>): void => {
    if (e.touches.length !== 1) {
      return;
    }
    touchStartXRef.current = e.touches[0].clientX;
    setDragPx(0);
  };

  const onTouchMove = (e: React.TouchEvent<HTMLDivElement>): void => {
    if (touchStartXRef.current === null || e.touches.length !== 1) {
      return;
    }
    const dx: number = e.touches[0].clientX - touchStartXRef.current;
    setDragPx(dx);
  };

  const onTouchEnd = (e: React.TouchEvent<HTMLDivElement>): void => {
    const start: number | null = touchStartXRef.current;
    touchStartXRef.current = null;
    if (start === null) {
      setDragPx(0);
      return;
    }
    const endX: number = e.changedTouches[0]?.clientX ?? start;
    const dx: number = endX - start;
    setDragPx(0);
    if (dx > SWIPE_PX) {
      goNext();
    } else if (dx < -SWIPE_PX) {
      goPrev();
    }
  };

  const onKeyDown = (e: React.KeyboardEvent<HTMLDivElement>): void => {
    if (e.key === "ArrowRight") {
      e.preventDefault();
      goNext();
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      goPrev();
    }
  };

  if (count === 0) {
    return (
      <div className="fast-swipe-empty muted" tabIndex={0}>
        Нет новостей в этой теме.
      </div>
    );
  }

  const shiftPercent: number = count > 0 ? (-activeIndex / count) * 100 : 0;

  return (
    <div className="fast-swipe-feed" aria-label="Быстрый режим: свайп вправо — далее, влево — назад">
      <div
        className="fast-swipe-viewport"
        onKeyDown={onKeyDown}
        onTouchEnd={onTouchEnd}
        onTouchMove={onTouchMove}
        onTouchStart={onTouchStart}
        role="region"
        tabIndex={0}
      >
        <div
          className={`fast-swipe-track${dragPx !== 0 ? " is-dragging" : ""}`}
          style={{
            transform: `translateX(calc(${shiftPercent}% + ${dragPx}px))`,
            width: `${Math.max(count, 1) * 100}%`
          }}
        >
          {items.map((item: NewsFeedItem) => (
            <div
              className="fast-swipe-slide"
              key={item.id}
              style={{ flex: `0 0 ${100 / Math.max(count, 1)}%` }}
            >
              <NewsCard feedMode="fast" item={item} variant="immersive" />
            </div>
          ))}
        </div>
      </div>
      <p className="fast-swipe-hint muted">
        Свайп вправо — следующая · влево — назад · стрелки на клавиатуре
      </p>
      <div className="fast-swipe-toolbar">
        <button disabled={activeIndex <= 0} onClick={goPrev} type="button">
          ← Назад
        </button>
        <span className="muted">
          {activeIndex + 1} / {count}
          {hasMore ? "+" : ""}
        </span>
        <button
          disabled={activeIndex >= count - 1 && (!hasMore || loadingMore)}
          onClick={goNext}
          type="button"
        >
          Далее →
        </button>
      </div>
    </div>
  );
}
