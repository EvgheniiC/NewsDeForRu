import topicCoversManifest from "../data/topicCoversManifest.json";
import type { CoverTag, NewsTopic } from "../types/news";

type TopicCoverManifest = Record<string, readonly string[]>;

const MANIFEST: TopicCoverManifest = topicCoversManifest as TopicCoverManifest;

/** Shown under topic covers (not publisher photos). */
export const TOPIC_COVER_AI_DISCLAIMER_RU: string = "Иллюстрация: ИИ";

function pickCoverPath(poolKey: string, newsId: number): string | null {
  const files: readonly string[] = MANIFEST[poolKey] ?? [];
  if (files.length === 0) {
    return null;
  }
  const index: number = Math.abs(Math.trunc(newsId)) % files.length;
  return `/topic-covers/${poolKey}/${files[index]}`;
}

/**
 * Stable cover URL for a news item.
 * Prefers the illustration tag folder; falls back to the public feed topic pool.
 */
export function newsTopicCoverSrc(
  topic: NewsTopic,
  newsId: number,
  coverTag?: CoverTag | null,
): string {
  if (coverTag) {
    const tagged: string | null = pickCoverPath(coverTag, newsId);
    if (tagged !== null) {
      return tagged;
    }
  }
  const fromTopic: string | null = pickCoverPath(topic, newsId);
  if (fromTopic !== null) {
    return fromTopic;
  }
  return `/topic-covers/${topic}/001.jpg`;
}
