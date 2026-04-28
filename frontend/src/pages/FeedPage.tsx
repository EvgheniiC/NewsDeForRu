import { useCallback, useEffect, useState } from "react";
import { FastSwipeFeed } from "../components/FastSwipeFeed";
import { GridFeed } from "../components/GridFeed";
import { TikTokFeed } from "../components/TikTokFeed";
import { ApiError, getHealth, NetworkError, runPipeline } from "../api/client";
import { useInfiniteFeed } from "../hooks/useInfiniteFeed";
import type { FeedFilterKey } from "../types/news";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";

type FeedViewMode = "grid" | "tiktok" | "fast";

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
  const [feedFilter, setFeedFilter] = useState<FeedFilterKey>("life");
  const [feedViewMode, setFeedViewMode] = useState<FeedViewMode>("grid");

  const { items, loading: feedLoading, loadingMore, feedError, nextCursor, reload, loadMore } =
    useInfiniteFeed(feedFilter);

  const hasMore: boolean = nextCursor !== null;
  /** Hide feed until first page for current topic; keep grid during refresh when data exists. */
  const feedBlocking: boolean = feedLoading && items.length === 0;

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

  useEffect(() => {
    void loadHealth();
  }, [loadHealth]);

  const handleRefresh = async (): Promise<void> => {
    setPipelineNetworkError("");
    setPipelineHttpError("");
    setPipelineRunning(true);
    try {
      const result: PipelineRunResponse = await runPipeline();
      setLastManualRun(result);
      await reload();
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

  const showDevPanels: boolean = feedViewMode === "grid";

  return (
    <section>
      <header className="page-header">
        <h1>Объясняем новости</h1>
        <button disabled={pipelineRunning} onClick={() => void handleRefresh()} type="button">
          {pipelineRunning ? "Выполняется pipeline…" : "Обновить через pipeline"}
        </button>
      </header>

      <div className="feed-topic-bar" role="tablist" aria-label="Темы ленты">
        {(
          [
            { key: "politics" as const, label: "Политика" },
            { key: "economy" as const, label: "Экономика" },
            { key: "life" as const, label: "Жизнь" },
            { key: "urgent" as const, label: "⚡ Срочно" }
          ] as const
        ).map((opt, index) => (
          <span key={opt.key} className="feed-topic-cell">
            {index > 0 ? <span className="feed-topic-sep" aria-hidden="true" /> : null}
            <button
              type="button"
              className={feedFilter === opt.key ? "feed-topic-pill is-active" : "feed-topic-pill"}
              role="tab"
              aria-selected={feedFilter === opt.key}
              onClick={() => {
                setFeedFilter(opt.key);
              }}
            >
              {opt.label}
            </button>
          </span>
        ))}
      </div>

      <div className="feed-view-bar" role="tablist" aria-label="Вид ленты">
        {(
          [
            { key: "grid" as const, label: "Сетка" },
            { key: "tiktok" as const, label: "Лента (вертикально)" },
            { key: "fast" as const, label: "Быстрый свайп" }
          ] as const
        ).map((opt, index) => (
          <span key={opt.key} className="feed-topic-cell">
            {index > 0 ? <span className="feed-topic-sep" aria-hidden="true" /> : null}
            <button
              type="button"
              className={feedViewMode === opt.key ? "feed-topic-pill is-active" : "feed-topic-pill"}
              role="tab"
              aria-selected={feedViewMode === opt.key}
              onClick={() => {
                setFeedViewMode(opt.key);
              }}
            >
              {opt.label}
            </button>
          </span>
        ))}
      </div>

      {showDevPanels && (
        <>
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
        </>
      )}

      {feedLoading && items.length === 0 && <p className="loading-inline">Загрузка ленты…</p>}
      {feedError && <p className="error">{feedError}</p>}

      {!feedBlocking && feedViewMode === "grid" && (
        <GridFeed
          feedLoading={feedLoading}
          hasMore={hasMore}
          items={items}
          loadingMore={loadingMore}
          onLoadMore={loadMore}
        />
      )}

      {!feedBlocking && feedViewMode === "tiktok" && (
        <TikTokFeed
          hasMore={hasMore}
          items={items}
          key={feedFilter}
          loadingMore={loadingMore}
          onLoadMore={loadMore}
        />
      )}

      {!feedBlocking && feedViewMode === "fast" && (
        <FastSwipeFeed
          hasMore={hasMore}
          items={items}
          key={feedFilter}
          loadingMore={loadingMore}
          onLoadMore={loadMore}
        />
      )}
    </section>
  );
}
