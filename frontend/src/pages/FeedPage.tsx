import { useCallback, useEffect, useState } from "react";
import { NewsCard } from "../components/NewsCard";
import { ApiError, getFeed, getHealth, NetworkError, runPipeline } from "../api/client";
import type { NewsFeedItem } from "../types/news";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";

function formatHealthTime(iso: string | null): string {
  if (!iso) {
    return "—";
  }
  try {
    const d: Date = new Date(iso);
    return new Intl.DateTimeFormat("ru-RU", {
      dateStyle: "short",
      timeStyle: "medium"
    }).format(d);
  } catch {
    return iso;
  }
}

export function FeedPage(): JSX.Element {
  const [items, setItems] = useState<NewsFeedItem[]>([]);
  const [feedError, setFeedError] = useState<string>("");
  const [feedLoading, setFeedLoading] = useState<boolean>(true);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string>("");

  const [pipelineRunning, setPipelineRunning] = useState<boolean>(false);
  const [lastManualRun, setLastManualRun] = useState<PipelineRunResponse | null>(null);
  const [pipelineNetworkError, setPipelineNetworkError] = useState<string>("");
  const [pipelineHttpError, setPipelineHttpError] = useState<string>("");

  const loadHealth = useCallback(async (): Promise<void> => {
    try {
      const h: HealthResponse = await getHealth();
      setHealth(h);
      setHealthError("");
    } catch (e: unknown) {
      const msg: string =
        e instanceof NetworkError
          ? `Сеть: ${e.message}`
          : e instanceof ApiError
            ? `Сервер: ${e.message}`
            : e instanceof Error
              ? e.message
              : "Не удалось загрузить /health.";
      setHealthError(msg);
    }
  }, []);

  const loadFeed = useCallback(async (): Promise<void> => {
    setFeedLoading(true);
    try {
      const response: NewsFeedItem[] = await getFeed();
      setItems(response);
      setFeedError("");
    } catch (e: unknown) {
      const msg: string =
        e instanceof NetworkError
          ? `Сеть: ${e.message}`
          : e instanceof ApiError
            ? `Сервер (${e.status}): ${e.message}`
            : e instanceof Error
              ? e.message
              : "Не удалось загрузить ленту.";
      setFeedError(msg);
    } finally {
      setFeedLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadFeed();
    void loadHealth();
  }, [loadFeed, loadHealth]);

  const handleRefresh = async (): Promise<void> => {
    setPipelineNetworkError("");
    setPipelineHttpError("");
    setPipelineRunning(true);
    try {
      const result: PipelineRunResponse = await runPipeline();
      setLastManualRun(result);
      await loadFeed();
      await loadHealth();
    } catch (e: unknown) {
      if (e instanceof NetworkError) {
        setPipelineNetworkError(e.message);
      } else if (e instanceof ApiError) {
        setPipelineHttpError(`${e.message} (HTTP ${e.status})`);
      } else {
        setPipelineHttpError(e instanceof Error ? e.message : "Неизвестная ошибка.");
      }
    } finally {
      setPipelineRunning(false);
    }
  };

  const pipelineOkMessage: string | null =
    lastManualRun !== null && !lastManualRun.ok && !lastManualRun.error
      ? "Пайплайн завершился с ok: false"
      : null;

  return (
    <section>
      <header className="page-header">
        <h1>Объясняем новости</h1>
        <button disabled={pipelineRunning} onClick={() => void handleRefresh()} type="button">
          {pipelineRunning ? "Выполняется pipeline…" : "Обновить через pipeline"}
        </button>
      </header>

      <div className="panel health-panel">
        <h2 className="panel-title">Состояние сервера</h2>
        {healthError && <p className="error">{healthError}</p>}
        {health && (
          <ul className="health-list">
            <li>
              <span className="health-label">Общий статус:</span>{" "}
              <span className={health.status === "ok" ? "health-ok" : "health-warn"}>{health.status}</span>
            </li>
            <li>
              <span className="health-label">База данных:</span>{" "}
              <span className={health.database === "ok" ? "health-ok" : "health-warn"}>{health.database}</span>
            </li>
            <li>
              <span className="health-label">Последний прогон пайплайна:</span>{" "}
              {formatHealthTime(health.last_pipeline_run_at)}
            </li>
            <li>
              <span className="health-label">Последний прогон успешен:</span>{" "}
              {health.last_pipeline_ok === null
                ? "—"
                : health.last_pipeline_ok
                  ? "да"
                  : "нет"}
            </li>
            <li>
              <span className="health-label">Планировщик:</span> {health.pipeline_scheduler}
            </li>
          </ul>
        )}
        {!health && !healthError && <p className="muted">Загрузка…</p>}
      </div>

      <div className="panel pipeline-panel">
        <h2 className="panel-title">Последний ручной запуск pipeline</h2>
        {pipelineNetworkError && <p className="error">Ошибка сети: {pipelineNetworkError}</p>}
        {pipelineHttpError && <p className="error">Ошибка HTTP: {pipelineHttpError}</p>}
        {lastManualRun === null && !pipelineNetworkError && !pipelineHttpError && !pipelineRunning && (
          <p className="muted">Ещё не запускали с этой страницы.</p>
        )}
        {pipelineRunning && <p className="loading-inline">Выполняется POST /pipeline/run…</p>}
        {pipelineOkMessage && <p className="error">{pipelineOkMessage}</p>}
        {lastManualRun !== null && (
          <dl className="pipeline-stats">
            <div>
              <dt>ok</dt>
              <dd className={lastManualRun.ok ? "health-ok" : "health-warn"}>{String(lastManualRun.ok)}</dd>
            </div>
            <div>
              <dt>error</dt>
              <dd>{lastManualRun.error ?? "—"}</dd>
            </div>
            <div>
              <dt>fetched</dt>
              <dd>{lastManualRun.fetched}</dd>
            </div>
            <div>
              <dt>feeds_failed</dt>
              <dd>{lastManualRun.feeds_failed}</dd>
            </div>
            <div>
              <dt>filtered_out</dt>
              <dd>{lastManualRun.filtered_out}</dd>
            </div>
            <div>
              <dt>clustered</dt>
              <dd>{lastManualRun.clustered}</dd>
            </div>
            <div>
              <dt>processed</dt>
              <dd>{lastManualRun.processed}</dd>
            </div>
            <div>
              <dt>published</dt>
              <dd>{lastManualRun.published}</dd>
            </div>
            <div>
              <dt>needs_review</dt>
              <dd>{lastManualRun.needs_review}</dd>
            </div>
            <div>
              <dt>item_errors</dt>
              <dd>{lastManualRun.item_errors}</dd>
            </div>
          </dl>
        )}
      </div>

      {feedLoading && <p className="loading-inline">Загрузка ленты…</p>}
      {feedError && <p className="error">{feedError}</p>}
      <div className={`news-grid ${feedLoading ? "news-grid-dim" : ""}`}>
        {items.map((item) => (
          <NewsCard item={item} key={item.id} />
        ))}
      </div>
    </section>
  );
}
