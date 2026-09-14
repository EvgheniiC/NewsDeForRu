import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, getHealth, getModerationQueue, moderate, NetworkError, patchNewsMetadata, runPipeline } from "../api/client";
import {
  ModerationMetadataForm,
  type NewsMetadataDraft,
} from "../components/ModerationMetadataForm";
import { ServerPipelinePanels } from "../components/ServerPipelinePanels";
import { useAuth } from "../context/AuthContext";
import { formatDateTimeRuBerlin } from "../lib/dateTimeBerlin";
import { describePipelinePartialFailure } from "../lib/pipelineUi";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";
import {
  countModerationQueueByPeriod,
  filterModerationQueueByPeriod,
  MODERATION_PERIOD_OPTIONS,
  type ModerationPeriodKey,
  type ModerationPeriodOption,
} from "../lib/moderationQueue";
import { NewsTopicCover } from "../components/NewsTopicCover";
import type { ProcessedNews } from "../types/news";

interface ModerationNewsCardProps {
  item: ProcessedNews;
  busyId: number | null;
  onAction: (newsId: number, action: "approve" | "reject") => void;
  onSaveMetadata: (newsId: number, draft: NewsMetadataDraft) => Promise<void>;
}

function ModerationNewsCard({
  item,
  busyId,
  onAction,
  onSaveMetadata,
}: ModerationNewsCardProps): JSX.Element {
  return (
    <article className="news-card">
      <p className="moderation-card-date">{formatDateTimeRuBerlin(item.created_at)}</p>
      <h3>{item.title}</h3>
      <NewsTopicCover newsId={item.id} topic={item.topic} variant="card" />
      <p>{item.one_sentence_summary}</p>
      <ModerationMetadataForm disabled={busyId !== null} item={item} onSave={onSaveMetadata} />
      <div className="news-card-footer">
        <button
          disabled={busyId !== null}
          onClick={() => {
            onAction(item.id, "approve");
          }}
          type="button"
        >
          Publish
        </button>
        <button
          disabled={busyId !== null}
          onClick={() => {
            onAction(item.id, "reject");
          }}
          type="button"
        >
          Reject
        </button>
      </div>
    </article>
  );
}

export function ModerationPage(): JSX.Element {
  const navigate = useNavigate();
  const { user, withModerationAccess, withPipelineAccess, logout } = useAuth();
  const [queue, setQueue] = useState<ProcessedNews[]>([]);
  const [period, setPeriod] = useState<ModerationPeriodKey>("today");
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string>("");
  const [actionError, setActionError] = useState<string>("");
  const [busyId, setBusyId] = useState<number | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string>("");
  const [pipelineRunning, setPipelineRunning] = useState<boolean>(false);
  const [lastManualRun, setLastManualRun] = useState<PipelineRunResponse | null>(null);
  const [pipelineNetworkError, setPipelineNetworkError] = useState<string>("");
  const [pipelineHttpError, setPipelineHttpError] = useState<string>("");
  const canRunPipeline: boolean = user?.can_run_pipeline === true;

  const periodCounts: Record<ModerationPeriodKey, number> = useMemo(
    () => countModerationQueueByPeriod(queue),
    [queue],
  );

  const visibleItems: ProcessedNews[] = useMemo(
    () => filterModerationQueueByPeriod(queue, period),
    [queue, period],
  );

  const loadQueue = useCallback(
    async (options?: { silent?: boolean }): Promise<void> => {
      const silent: boolean = options?.silent ?? false;
      if (!silent) {
        setLoading(true);
      }
      try {
        const data: ProcessedNews[] = await withModerationAccess(async (token: string) =>
          getModerationQueue(token),
        );
        setQueue(data);
        setError("");
      } catch (fetchError: unknown) {
        if (fetchError instanceof ApiError && fetchError.status === 401) {
          await logout();
          navigate("/login", { replace: true, state: { from: "/moderation" } });
          return;
        }
        setError(fetchError instanceof Error ? fetchError.message : "Не удалось загрузить очередь.");
      } finally {
        if (!silent) {
          setLoading(false);
        }
      }
    },
    [logout, navigate, withModerationAccess],
  );

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
    if (!user?.can_moderate) {
      return;
    }
    void loadQueue();
    void loadHealth();
  }, [loadHealth, loadQueue, user?.can_moderate]);

  const handlePipelineRefresh = async (): Promise<void> => {
    setPipelineNetworkError("");
    setPipelineHttpError("");
    setPipelineRunning(true);
    try {
      const result: PipelineRunResponse = await withPipelineAccess((token: string) => runPipeline(token));
      setLastManualRun(result);
      await loadQueue({ silent: true });
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
    lastManualRun !== null ? describePipelinePartialFailure(lastManualRun) : null;

  const handleAction = async (newsId: number, action: "approve" | "reject"): Promise<void> => {
    setActionError("");
    setBusyId(newsId);
    try {
      await withModerationAccess(async (token: string) => moderate(newsId, action, token));
      await loadQueue({ silent: true });
    } catch (fetchError: unknown) {
      if (fetchError instanceof ApiError && fetchError.status === 401) {
        await logout();
        navigate("/login", { replace: true, state: { from: "/moderation" } });
        return;
      }
      setActionError(
        fetchError instanceof Error ? fetchError.message : "Не удалось выполнить действие.",
      );
    } finally {
      setBusyId(null);
    }
  };

  const handleSaveMetadata = async (newsId: number, draft: NewsMetadataDraft): Promise<void> => {
    const current: ProcessedNews | undefined = queue.find((item: ProcessedNews) => item.id === newsId);
    if (current === undefined) {
      throw new Error("Новость не найдена в очереди.");
    }

    const patch: {
      topic?: NewsMetadataDraft["topic"];
      is_urgent?: boolean;
      is_positive?: boolean;
    } = {};
    if (draft.topic !== current.topic) {
      patch.topic = draft.topic;
    }
    if (draft.is_urgent !== current.is_urgent) {
      patch.is_urgent = draft.is_urgent;
    }
    if (draft.is_positive !== current.is_positive) {
      patch.is_positive = draft.is_positive;
    }

    const updated: ProcessedNews = await withModerationAccess(async (token: string) =>
      patchNewsMetadata(newsId, patch, token),
    );
    setQueue((items: ProcessedNews[]) =>
      items.map((item: ProcessedNews) => (item.id === newsId ? updated : item)),
    );
  };

  return (
    <section>
      <h1>Модерация</h1>
      <p className="moderation-queue-hint">
        Показаны новости за последние 7 дней. Старше недели в очереди не отображаются.
      </p>

      <ServerPipelinePanels
        canRunPipeline={canRunPipeline}
        health={health}
        healthError={healthError}
        lastManualRun={lastManualRun}
        pipelineHttpError={pipelineHttpError}
        pipelineNetworkError={pipelineNetworkError}
        pipelineOkMessage={pipelineOkMessage}
        pipelineRunning={pipelineRunning}
        onRefresh={() => {
          void handlePipelineRefresh();
        }}
      />

      <div className="feed-period-bar moderation-period-bar" role="tablist" aria-label="Период модерации">
        {MODERATION_PERIOD_OPTIONS.map((opt: ModerationPeriodOption) => (
          <button
            key={opt.key}
            aria-selected={period === opt.key}
            className={period === opt.key ? "feed-topic-pill is-active" : "feed-topic-pill"}
            onClick={() => {
              setPeriod(opt.key);
            }}
            role="tab"
            type="button"
          >
            {opt.label}
            <span className="moderation-period-count">{periodCounts[opt.key]}</span>
          </button>
        ))}
      </div>

      {loading && <p>Загрузка...</p>}
      {error !== "" && <p className="error">{error}</p>}
      {actionError !== "" && <p className="error">{actionError}</p>}
      {!loading && error === "" && queue.length === 0 && <p>Очередь пуста.</p>}
      {!loading && error === "" && queue.length > 0 && visibleItems.length === 0 && (
        <p>Нет новостей за выбранный период.</p>
      )}
      {!loading && error === "" && visibleItems.length > 0 && (
        <div className="news-grid">
          {visibleItems.map((item: ProcessedNews) => (
            <ModerationNewsCard
              busyId={busyId}
              item={item}
              key={item.id}
              onAction={(newsId: number, action: "approve" | "reject") => {
                void handleAction(newsId, action);
              }}
              onSaveMetadata={handleSaveMetadata}
            />
          ))}
        </div>
      )}
    </section>
  );
}
