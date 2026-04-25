import { useEffect, useState } from "react";
import { NewsCard } from "../components/NewsCard";
import { getFeed, runPipeline } from "../api/client";
import type { NewsFeedItem } from "../types/news";

export function FeedPage(): JSX.Element {
  const [items, setItems] = useState<NewsFeedItem[]>([]);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(true);

  const loadFeed = async (): Promise<void> => {
    setLoading(true);
    try {
      const response: NewsFeedItem[] = await getFeed();
      setItems(response);
      setError("");
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : "Не удалось загрузить ленту.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadFeed();
  }, []);

  const handleRefresh = async (): Promise<void> => {
    try {
      setError("");
      await runPipeline();
      await loadFeed();
    } catch (fetchError: unknown) {
      setError(fetchError instanceof Error ? fetchError.message : "Не удалось обновить данные.");
    }
  };

  return (
    <section>
      <header className="page-header">
        <h1>Объясняем новости</h1>
        <button onClick={() => void handleRefresh()} type="button">
          Обновить через pipeline
        </button>
      </header>
      {loading && <p>Загрузка...</p>}
      {error && <p className="error">{error}</p>}
      <div className="news-grid">
        {items.map((item) => (
          <NewsCard item={item} key={item.id} />
        ))}
      </div>
    </section>
  );
}
