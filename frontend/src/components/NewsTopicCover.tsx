import { TOPIC_COVER_AI_DISCLAIMER_RU, newsTopicCoverSrc } from "../lib/topicCovers";
import type { NewsTopic } from "../types/news";

interface NewsTopicCoverProps {
  topic: NewsTopic;
  newsId: number;
  /** ``card`` for feed/moderation; ``detail`` for the article page. */
  variant?: "card" | "detail";
}

/** Topic-pool illustration with AI disclaimer (not a publisher photo). */
export function NewsTopicCover({
  topic,
  newsId,
  variant = "card"
}: NewsTopicCoverProps): JSX.Element {
  const imageClass: string = variant === "detail" ? "news-detail-image" : "news-card-image";
  const wrapClass: string =
    variant === "detail" ? "news-topic-cover news-topic-cover--detail" : "news-topic-cover";

  return (
    <figure className={wrapClass}>
      <img alt="" className={imageClass} decoding="async" loading="lazy" src={newsTopicCoverSrc(topic, newsId)} />
      <figcaption className="news-topic-cover__disclaimer">{TOPIC_COVER_AI_DISCLAIMER_RU}</figcaption>
    </figure>
  );
}
