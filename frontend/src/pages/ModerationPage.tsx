import { useEffect, useState } from "react";
import { getModerationQueue, moderate } from "../api/client";
import type { ProcessedNews } from "../types/news";

export function ModerationPage(): JSX.Element {
  const [queue, setQueue] = useState<ProcessedNews[]>([]);

  const loadQueue = async (): Promise<void> => {
    const data: ProcessedNews[] = await getModerationQueue();
    setQueue(data);
  };

  useEffect(() => {
    void loadQueue();
  }, []);

  const handleAction = async (newsId: number, action: "approve" | "reject"): Promise<void> => {
    await moderate(newsId, action);
    await loadQueue();
  };

  return (
    <section>
      <h1>Модерация</h1>
      {queue.length === 0 && <p>Очередь пуста.</p>}
      <div className="news-grid">
        {queue.map((item) => (
          <article className="news-card" key={item.id}>
            <h3>{item.title}</h3>
            <p>{item.one_sentence_summary}</p>
            <div className="news-card-footer">
              <button onClick={() => void handleAction(item.id, "approve")} type="button">
                Publish
              </button>
              <button onClick={() => void handleAction(item.id, "reject")} type="button">
                Reject
              </button>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
