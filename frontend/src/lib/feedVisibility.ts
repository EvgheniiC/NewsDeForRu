import { readStoredUseful } from "./usefulStorage";
import { isNewsRead } from "./readStateStorage";
import type { FeedFilterKey, NewsFeedItem } from "../types/news";

const MS_PER_DAY: number = 24 * 60 * 60 * 1000;

/** Max age in the active feed when the user takes no action. */
export function activeFeedMaxAgeDays(filter: FeedFilterKey): number {
  switch (filter) {
    case "top_today":
      return 1;
    case "urgent":
      return 2;
    case "saved_useful":
    case "read_saved":
      return 0;
    default:
      return 3;
  }
}

export function isWithinActiveFeedTtl(item: NewsFeedItem, filter: FeedFilterKey): boolean {
  const maxDays: number = activeFeedMaxAgeDays(filter);
  if (maxDays <= 0) {
    return true;
  }
  const publishedMs: number = new Date(item.published_at).getTime();
  if (!Number.isFinite(publishedMs)) {
    return true;
  }
  return Date.now() - publishedMs <= maxDays * MS_PER_DAY;
}

export function isHiddenFromActiveFeed(item: NewsFeedItem): boolean {
  return readStoredUseful(item.id) || isNewsRead(item.id);
}

export function filterActiveFeedItems(items: NewsFeedItem[], filter: FeedFilterKey): NewsFeedItem[] {
  return items.filter(
    (item: NewsFeedItem) => !isHiddenFromActiveFeed(item) && isWithinActiveFeedTtl(item, filter)
  );
}

export function isAllReadInFetchedBatch(items: NewsFeedItem[]): boolean {
  if (items.length === 0) {
    return false;
  }
  return items.every((item: NewsFeedItem) => isNewsRead(item.id) || readStoredUseful(item.id));
}

/** True when the server returned items but none are visible (read, saved, or past TTL). */
export function isFeedCaughtUp(items: NewsFeedItem[], filter: FeedFilterKey): boolean {
  if (items.length === 0) {
    return false;
  }
  return filterActiveFeedItems(items, filter).length === 0;
}
