import { Link } from "react-router-dom";
import type { NewsFeedItem } from "../types/news";

interface NewsCardProps {
  item: NewsFeedItem;
}

export function NewsCard({ item }: NewsCardProps): JSX.Element {
  return (
    <article className="news-card">
      {item.is_urgent ? <span className="news-urgent-badge">⚡ Срочно</span> : null}
      <h3>{item.title}</h3>
      <p>{item.subtitle}</p>
      <div className="news-card-footer">
        <span>⏱ {item.read_time_minutes} мин</span>
        <Link to={`/news/${item.id}`}>Открыть</Link>
      </div>
    </article>
  );
}
