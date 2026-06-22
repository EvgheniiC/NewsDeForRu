import type { FeedFilterKey, NewsFeedItem, NewsTopic } from "../types/news";

export type NewsCardLayoutVariant = "compact" | "immersive";

/** BEM-style chip class for topic-colored labels. */
export function newsTopicChipClass(topic: NewsTopic): string {
  return `news-topic-chip news-topic-chip--${topic}`;
}

const FEED_FILTER_ACCENT_CLASS: Partial<Record<FeedFilterKey, string>> = {
  top_today: "is-accent-top",
  politics: "is-accent-politics",
  economy: "is-accent-economy",
  life: "is-accent-life",
  urgent: "is-accent-urgent",
  positive: "is-accent-positive",
  saved_useful: "is-accent-saved"
};

/** Active feed topic tab with semantic accent color. */
export function feedFilterPillClass(filter: FeedFilterKey, isActive: boolean): string {
  if (!isActive) {
    return "feed-topic-pill";
  }
  const accent: string = FEED_FILTER_ACCENT_CLASS[filter] ?? "";
  return accent === "" ? "feed-topic-pill is-active" : `feed-topic-pill is-active ${accent}`;
}

/** Card root classes including urgency / positivity / top-rank modifiers. */
export function newsCardClassName(item: NewsFeedItem, variant: NewsCardLayoutVariant): string {
  const parts: string[] = ["news-card"];
  if (variant === "immersive") {
    parts.push("news-card-immersive");
  }
  if (item.is_urgent) {
    parts.push("news-card--urgent");
  }
  if (item.is_positive) {
    parts.push("news-card--positive");
  }
  if (item.rank) {
    parts.push("news-card--top");
  }
  return parts.join(" ");
}
