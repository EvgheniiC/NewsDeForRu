import { useEffect, useState } from "react";
import { getModerationQueue, moderate } from "../api/client";
import { newsTopicLabelRu, type ProcessedNews } from "../types/news";

export function ModerationPage(): JSX.Element {
  const [queue, setQueue] = useState<ProcessedNews[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [actionError, setActionError] = useState<string>("");
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadQueue = async (options?: { silent?: boolean }): Promise<void> => {
    const silent: boolean = options?.silent ?? false;
    if (!silent) {
      setLoading(true);
    }
    try {
      const data: ProcessedNews[] = await getModerationQueue();
      setQueue(data);
      setError("");
    } catch (fetchError: unknown) {
      setError(fetchError instanceof Error ? fetchError.message : "Не удалось загрузить очередь.");
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  useEffect(() => {
    void loadQueue();
  }, []);

  const handleAction = async (newsId: number, action: "approve" | "reject"): Promise<void> => {
    setActionError("");
    setBusyId(newsId);
    try {
      await moderate(newsId, action);
      await loadQueue({ silent: true });
    } catch (fetchError: unknown) {
      setActionError(
        fetchError instanceof Error ? fetchError.message : "Не удалось выполнить действие.",
      );
    } finally {
      setBusyId(null);
    }
  };

  return (
    <section>
      <h1>Модерация</h1>
      {loading && <p>Загрузка...</p>}
      {error && <p className="error">{error}</p>}
      {actionError && <p className="error">{actionError}</p>}
      {!loading && !error && queue.length === 0 && <p>Очередь пуста.</p>}
      <div className="news-grid">
        {queue.map((item: ProcessedNews) => (
          <article className="news-card" key={item.id}>
            <h3>{item.title}</h3>
            {item.image_url ? (
              <img
                alt={item.title}
                className="news-card-image"
                decoding="async"
                loading="lazy"
                src={item.image_url}
              />
            ) : null}
            <p>{item.one_sentence_summary}</p>
            <div className="news-card-footer">
              <button
                disabled={busyId !== null}
                onClick={() => void handleAction(item.id, "approve")}
                type="button"
              >
                Publish
              </button>
              <button
                disabled={busyId !== null}
                onClick={() => void handleAction(item.id, "reject")}
                type="button"
              >
                Reject
              </button>
            </div>
            <div className="news-card-topic-row">
              <span className="news-topic-label">{newsTopicLabelRu(item.topic)}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
