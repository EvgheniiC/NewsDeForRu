import { Link } from "react-router-dom";
import type { NewsFeedItem } from "../types/news";

export type NewsCardVariant = "compact" | "immersive";

interface NewsCardProps {
  item: NewsFeedItem;
  variant?: NewsCardVariant;
}

export function NewsCard({ item, variant = "compact" }: NewsCardProps): JSX.Element {
  const rootClass: string = variant === "immersive" ? "news-card news-card-immersive" : "news-card";
  return (
    <article className={rootClass}>
      {item.is_urgent ? <span className="news-urgent-badge">⚡ Срочно</span> : null}
      <h3>{item.title}</h3>
      <p className={variant === "immersive" ? "news-card-subtitle-immersive" : undefined}>{item.subtitle}</p>
      <div className="news-card-footer">
        <span>⏱ {item.read_time_minutes} мин</span>
        <Link to={`/news/${item.id}`}>Открыть</Link>
      </div>
    </article>
  );
}
