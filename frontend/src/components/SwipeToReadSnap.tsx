import { useRef, useState, type ReactNode } from "react";
import { markNewsAsRead } from "../lib/readStateStorage";
import type { NewsFeedItem } from "../types/news";

const SWIPE_PX: number = 56;

interface SwipeToReadSnapProps {
  item: NewsFeedItem;
  children: ReactNode;
  className?: string;
  dataNewsId?: string;
}

/** Wraps a feed card; horizontal swipe right marks the news as read. */
export function SwipeToReadSnap({
  item,
  children,
  className,
  dataNewsId
}: SwipeToReadSnapProps): JSX.Element {
  const touchStartXRef: { current: number | null } = useRef<number | null>(null);
  const [dragPx, setDragPx] = useState<number>(0);
  const [dismissing, setDismissing] = useState<boolean>(false);

  const resetTouch = (): void => {
    touchStartXRef.current = null;
    setDragPx(0);
  };

  const onTouchStart = (e: React.TouchEvent<HTMLDivElement>): void => {
    if (e.touches.length !== 1 || dismissing) {
      return;
    }
    touchStartXRef.current = e.touches[0].clientX;
    setDragPx(0);
  };

  const onTouchMove = (e: React.TouchEvent<HTMLDivElement>): void => {
    if (touchStartXRef.current === null || e.touches.length !== 1 || dismissing) {
      return;
    }
    const dx: number = e.touches[0].clientX - touchStartXRef.current;
    if (dx > 0) {
      setDragPx(dx);
    }
  };

  const onTouchEnd = (e: React.TouchEvent<HTMLDivElement>): void => {
    const start: number | null = touchStartXRef.current;
    if (start === null || dismissing) {
      resetTouch();
      return;
    }
    const endX: number = e.changedTouches[0]?.clientX ?? start;
    const dx: number = endX - start;
    resetTouch();
    if (dx > SWIPE_PX) {
      setDismissing(true);
      markNewsAsRead(item.id);
    }
  };

  const rootClass: string = [className, dismissing ? "swipe-to-read-snap is-dismissing" : "swipe-to-read-snap"]
    .filter(Boolean)
    .join(" ");

  return (
    <div
      className={rootClass}
      data-news-id={dataNewsId}
      onTouchEnd={onTouchEnd}
      onTouchMove={onTouchMove}
      onTouchStart={onTouchStart}
      style={dragPx > 0 ? { transform: `translateX(${Math.min(dragPx, 120)}px)`, opacity: `${1 - dragPx / 240}` } : undefined}
    >
      {children}
    </div>
  );
}
