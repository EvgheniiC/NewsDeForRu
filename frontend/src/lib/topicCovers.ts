import topicCoversManifest from "../data/topicCoversManifest.json";
import type { NewsTopic } from "../types/news";

type TopicCoverManifest = Record<NewsTopic, readonly string[]>;

const MANIFEST: TopicCoverManifest = topicCoversManifest as TopicCoverManifest;

/** Shown under topic covers (not publisher photos). */
export const TOPIC_COVER_AI_DISCLAIMER_RU: string = "Иллюстрация: ИИ";

/**
 * Stable cover URL for a news item from the topic pool.
 * Keep file lists in sync with ``frontend/public/topic-covers/`` and backend manifest.
 */
export function newsTopicCoverSrc(topic: NewsTopic, newsId: number): string {
  const files: readonly string[] = MANIFEST[topic] ?? [];
  if (files.length === 0) {
    return `/topic-covers/${topic}/001.jpg`;
  }
  const index: number = Math.abs(Math.trunc(newsId)) % files.length;
  return `/topic-covers/${topic}/${files[index]}`;
}
