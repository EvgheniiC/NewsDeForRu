export type NewsTopic = "politics" | "economy" | "life";

/** Human-readable topic label for the UI (Russian). */
export function newsTopicLabelRu(topic: NewsTopic): string {
  switch (topic) {
    case "politics":
      return "Политика";
    case "economy":
      return "Экономика";
    case "life":
      return "Жизнь";
    default: {
      const _exhaustive: never = topic;
      return _exhaustive;
    }
  }
}

/** How the impact block is shown: three angles, one paragraph, or hidden. */
export type ImpactPresentation = "multi" | "single" | "none";

export type FeedFilterKey = NewsTopic | "urgent" | "positive" | "top_today" | "saved_useful" | "read_saved";

/** Labels for multi-perspective impact blocks on the detail page. */
export const IMPACT_PERSPECTIVE_LABELS: readonly string[] = [
  "Для собственника",
  "Для арендатора",
  "Для покупателя"
] as const;

/** Matches GET /news ``period``; ``all`` omits the query param. */
export type FeedPeriodKey = "all" | "today" | "last_3_days" | "this_week" | "this_month";

/** Breakdown from GET /news/top-today scoring. */
export interface TopNewsRankMeta {
  total_score: number;
  source_count: number;
  mentions_points: number;
  freshness_points: number;
  ai_importance: number;
}

export interface NewsFeedItem {
  id: number;
  title: string;
  subtitle: string;
  /** Legacy publisher preview URL; UI uses topic stock covers instead. */
  image_url?: string | null;
  read_time_minutes: number;
  topic: NewsTopic;
  is_urgent: boolean;
  is_positive: boolean;
  published_at: string;
  source_name: string;
  created_at: string;
  rank?: TopNewsRankMeta;
}

/** Health of the publisher article URL. */
export type SourceUrlStatus = "alive" | "unavailable" | "unknown";

export interface ProcessedNews {
  id: number;
  title: string;
  one_sentence_summary: string;
  plain_language: string;
  /** Omitted in older API responses; treat as "multi" if missing. */
  impact_presentation?: ImpactPresentation;
  impact_unified?: string;
  impact_owner: string;
  impact_tenant: string;
  impact_buyer: string;
  action_items: string;
  bonus_block: string;
  spoiler: string;
  source_url: string;
  /** Link health from daily check; omitted in older API responses. */
  source_url_status?: SourceUrlStatus;
  image_url?: string | null;
  confidence_score: number;
  publication_status: string;
  read_time_minutes: number;
  topic: NewsTopic;
  is_urgent: boolean;
  is_positive: boolean;
  published_at: string;
  source_name: string;
  original_title?: string | null;
  original_language?: string | null;
  retrieved_at?: string | null;
  licence?: string | null;
  licence_url?: string | null;
  copyright_holder?: string | null;
  is_translated?: boolean;
  is_ai_summarised?: boolean;
  changes_notice?: string | null;
  third_party_material_excluded?: boolean;
  source_revision?: string | null;
  created_at: string;
}

export function processedNewsToFeedItem(p: ProcessedNews): NewsFeedItem {
  return {
    id: p.id,
    title: p.title,
    subtitle: p.one_sentence_summary,
    image_url: p.image_url ?? null,
    read_time_minutes: p.read_time_minutes,
    topic: p.topic,
    is_urgent: p.is_urgent,
    is_positive: p.is_positive,
    published_at: p.published_at,
    source_name: p.source_name,
    created_at: p.created_at
  };
}
