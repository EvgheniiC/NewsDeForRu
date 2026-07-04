import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Capacitor } from "@capacitor/core";
import { CompactSelect } from "../components/CompactSelect";
import { TikTokFeed } from "../components/TikTokFeed";
import { ApiError, getHealth, NetworkError, runPipeline } from "../api/client";
import { useAuth } from "../context/AuthContext";
import { useInfiniteFeed } from "../hooks/useInfiniteFeed";
import { useReadSavedFeed } from "../hooks/useReadSavedFeed";
import { useUsefulSavedFeed } from "../hooks/useUsefulSavedFeed";
import { filterActiveFeedItems, isAllReadInFetchedBatch } from "../lib/feedVisibility";
import { feedFilterPillClass } from "../lib/newsUi";
import { describePipelinePartialFailure, formatHealthTime } from "../lib/pipelineUi";
import { READ_STATE_CHANGED_EVENT } from "../lib/readStateStorage";
import { flushPendingScrollRead, isWebScrollToReadEnabled } from "../lib/scrollToRead";
import { USEFUL_STORAGE_CHANGED_EVENT } from "../lib/usefulStorage";
import type { FeedFilterKey, FeedPeriodKey } from "../types/news";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";

const FEED_TOPIC_ROWS: readonly (readonly { key: FeedFilterKey; label: string }[])[] = [
  [
    { key: "top_today", label: "🔥 Топ-5" },
    { key: "urgent", label: "⚡ Срочно" },
    { key: "positive", label: "☀️ ТПН" }
  ],
  [
    { key: "economy", label: "Экономика" },
    { key: "life", label: "Жизнь" },
    { key: "politics", label: "Политика" }
  ],
  [{ key: "saved_useful", label: "❤️ Полезные" }, { key: "read_saved", label: "📖 Прочитанные" }]
];

const FEED_PERIOD_OPTIONS: readonly { key: FeedPeriodKey; label: string }[] = [
  { key: "all", label: "Всё время" },
  { key: "today", label: "Сегодня" },
  { key: "last_3_days", label: "3 дня" },
  { key: "this_week", label: "Неделя" },
  { key: "this_month", label: "Месяц" }
];

interface FeedLocationState {
  verificationPendingEmail?: string;
  devVerificationLink?: string | null;
}

export function FeedPage(): JSX.Element {
  const location = useLocation();
  const navigate = useNavigate();
  const feedLocationState = location.state as FeedLocationState | null | undefined;
  const verificationPendingEmail: string = feedLocationState?.verificationPendingEmail?.trim() ?? "";
  const devVerificationLink: string | null =
    typeof feedLocationState?.devVerificationLink === "string" && feedLocationState.devVerificationLink.length > 0
      ? feedLocationState.devVerificationLink
      : null;
  const { initializing: sessionLoading, user, withPipelineAccess } = useAuth();
  const [feedFilter, setFeedFilter] = useState<FeedFilterKey>("life");
  const [feedPeriod, setFeedPeriod] = useState<FeedPeriodKey>("all");
  const [feedVisibilityRevision, setFeedVisibilityRevision] = useState<number>(0);

  const isSavedUsefulTab: boolean = feedFilter === "saved_useful";
  const isReadSavedTab: boolean = feedFilter === "read_saved";
  const isArchiveTab: boolean = isSavedUsefulTab || isReadSavedTab;
  /** Placeholder topic when archive tabs disable infinite scrolling; no requests are sent (`enabled: false`). */
  const infiniteFeedFilter: Exclude<FeedFilterKey, "saved_useful" | "read_saved"> =
    isArchiveTab ? "life" : feedFilter;

  const { items: infiniteItems, loading: infiniteLoading, loadingMore, feedError: infiniteFeedError, nextCursor, reload, loadMore } =
    useInfiniteFeed(infiniteFeedFilter, feedPeriod, { enabled: !isArchiveTab });

  const {
    items: savedItems,
    loading: savedLoading,
    feedError: savedFeedError,
    refresh: refreshSavedUseful
  } = useUsefulSavedFeed(isSavedUsefulTab);

  const {
    items: readItems,
    loading: readLoading,
    feedError: readFeedError,
    refresh: refreshReadSaved
  } = useReadSavedFeed(isReadSavedTab);

  const rawItems = isSavedUsefulTab ? savedItems : isReadSavedTab ? readItems : infiniteItems;
  const visibleItems = isArchiveTab ? rawItems : filterActiveFeedItems(rawItems, feedFilter);
  const feedLoading = isSavedUsefulTab ? savedLoading : isReadSavedTab ? readLoading : infiniteLoading;
  const feedError = isSavedUsefulTab ? savedFeedError : isReadSavedTab ? readFeedError : infiniteFeedError;

  useEffect(() => {
    const bumpRevision = (): void => {
      setFeedVisibilityRevision((value: number) => value + 1);
    };
    window.addEventListener(READ_STATE_CHANGED_EVENT, bumpRevision);
    window.addEventListener(USEFUL_STORAGE_CHANGED_EVENT, bumpRevision);
    return (): void => {
      window.removeEventListener(READ_STATE_CHANGED_EVENT, bumpRevision);
      window.removeEventListener(USEFUL_STORAGE_CHANGED_EVENT, bumpRevision);
    };
  }, []);

  const hasMore: boolean = !isArchiveTab && nextCursor !== null;
  /** Hide feed until first page for current topic; keep grid during refresh when data exists. */
  const feedBlocking: boolean = feedLoading && visibleItems.length === 0;
  const allReadInCategory: boolean =
    !isArchiveTab &&
    !feedLoading &&
    !feedError &&
    infiniteItems.length > 0 &&
    visibleItems.length === 0 &&
    isAllReadInFetchedBatch(infiniteItems);
  const isNativeApp: boolean = Capacitor.isNativePlatform();
  const scrollToRead: boolean = !isArchiveTab && isWebScrollToReadEnabled();
  const swipeToRead: boolean = !isArchiveTab && isNativeApp;
  const showFeedReadHint: boolean = !isArchiveTab;
  const feedReadHint: string = isNativeApp
    ? "Свайп вправо, если прочли новость, не открывая её."
    : "Пролистанные новости попадают в «Прочитанные» — открывать их не обязательно.";

  useEffect(() => {
    if (!scrollToRead) {
      return;
    }
    const onPageHide = (): void => {
      flushPendingScrollRead();
    };
    window.addEventListener("pagehide", onPageHide);
    flushPendingScrollRead();
    return (): void => {
      window.removeEventListener("pagehide", onPageHide);
      flushPendingScrollRead();
    };
  }, [scrollToRead, feedFilter, feedPeriod]);

  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthError, setHealthError] = useState<string>("");

  const [pipelineRunning, setPipelineRunning] = useState<boolean>(false);
  const [lastManualRun, setLastManualRun] = useState<PipelineRunResponse | null>(null);
  const [pipelineNetworkError, setPipelineNetworkError] = useState<string>("");
  const [pipelineHttpError, setPipelineHttpError] = useState<string>("");

  const canRunPipeline: boolean = !sessionLoading && user?.can_run_pipeline === true;

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
    if (!canRunPipeline) {
      setHealth(null);
      setHealthError("");
      return;
    }
    void loadHealth();
  }, [loadHealth, canRunPipeline]);

  const handleRefresh = async (): Promise<void> => {
    setPipelineNetworkError("");
    setPipelineHttpError("");
    setPipelineRunning(true);
    try {
      const result: PipelineRunResponse = await withPipelineAccess((token: string) => runPipeline(token));
      setLastManualRun(result);
      await reload();
      if (feedFilter === "saved_useful") {
        await refreshSavedUseful();
      }
      if (feedFilter === "read_saved") {
        await refreshReadSaved();
      }
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

  const showDevPanels: boolean = !isArchiveTab && canRunPipeline;

  const dismissVerificationNotice = (): void => {
    navigate(location.pathname, { replace: true, state: null });
  };

  return (
    <section>
      {verificationPendingEmail !== "" ? (
        <div className="account-form-card feed-verification-notice">
          <h2>Подтвердите email</h2>
          <p>
            Мы отправили ссылку на <strong>{verificationPendingEmail}</strong>. Откройте письмо и нажмите ссылку,
            чтобы активировать аккаунт.
          </p>
          <p className="muted">Если письма нет, проверьте папку «Спам».</p>
          {devVerificationLink !== null ? (
            <p className="muted">
              Режим разработки (SMTP не настроен):{" "}
              <a href={devVerificationLink}>открыть ссылку подтверждения</a>
            </p>
          ) : null}
          <p className="account-forgot-link">
            <Link to="/account/resend-verification">Отправить ссылку повторно</Link>
          </p>
          <p className="account-mode-toggle">
            <button onClick={dismissVerificationNotice} type="button">
              Скрыть
            </button>
          </p>
        </div>
      ) : null}

      <div className="feed-topic-bar" role="tablist" aria-label="Темы ленты">
        {FEED_TOPIC_ROWS.map((row, rowIndex: number) => (
          <div key={rowIndex} className="feed-topic-row">
            {row.map((opt) => (
              <button
                key={opt.key}
                type="button"
                className={feedFilterPillClass(opt.key, feedFilter === opt.key)}
                role="tab"
                aria-selected={feedFilter === opt.key}
                onClick={() => {
                  setFeedFilter(opt.key);
                }}
              >
                {opt.label}
              </button>
            ))}
          </div>
        ))}
        {showFeedReadHint ? (
          <p className="feed-swipe-hint muted">{feedReadHint}</p>
        ) : null}
      </div>

      {feedFilter !== "top_today" && !isArchiveTab ? (
        <div className="feed-controls-bar">
          <CompactSelect
            ariaLabel="Период"
            onChange={(value: FeedPeriodKey) => {
              setFeedPeriod(value);
            }}
            options={FEED_PERIOD_OPTIONS}
            value={feedPeriod}
          />
        </div>
      ) : null}

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
                  <span className="health-label">Run ID последнего прогона:</span>{" "}
                  <code className="health-code">{health.last_pipeline_run_id ?? "—"}</code>
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
            <button disabled={pipelineRunning} onClick={() => void handleRefresh()} type="button">
              {pipelineRunning ? "Выполняется pipeline…" : "Обновить через pipeline"}
            </button>
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
                  <dt>run_id</dt>
                  <dd>
                    <code>{lastManualRun.run_id}</code>
                  </dd>
                </div>
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
                {lastManualRun.item_error_details.length > 0 ? (
                  <div className="pipeline-item-errors">
                    <dt>item_error_details</dt>
                    <dd>
                      <pre className="pipeline-error-json">
                        {JSON.stringify(lastManualRun.item_error_details, null, 2)}
                      </pre>
                    </dd>
                  </div>
                ) : null}
              </dl>
            )}
          </div>
        </>
      )}

      {feedFilter === "positive" ? (
        <h2 className="feed-section-heading feed-section-heading--positive">☀️ Только Позитивные Новости (ТПН)</h2>
      ) : null}

      {feedLoading && visibleItems.length === 0 && <p className="loading-inline">Загрузка ленты…</p>}
      {feedError && <p className="error">{feedError}</p>}
      {allReadInCategory ? (
        <div className="feed-empty-state">
          <p>В этой категории всё прочитано.</p>
          <p className="muted">
            Открытые статьи тоже попадают в «Прочитанные».{" "}
            <button
              className="feed-empty-state-link"
              onClick={() => {
                setFeedFilter("read_saved");
              }}
              type="button"
            >
              Перейти в «Прочитанные»
            </button>
          </p>
        </div>
      ) : null}
      {!feedLoading && !feedError && !isArchiveTab && !allReadInCategory && visibleItems.length === 0 ? (
        <div className="feed-empty-state">
          <p>Сейчас в этой подборке нет новостей. Лента обновляется автоматически — попробуйте позже или обновите вручную.</p>
          <button disabled={feedLoading} onClick={() => void reload()} type="button">
            Обновить ленту
          </button>
        </div>
      ) : null}
      {isSavedUsefulTab && !feedLoading && visibleItems.length === 0 && !feedError ? (
        <p className="muted">
          Здесь появятся новости, отмеченные «Полезно». Хранятся 60 дней на этом устройстве, на сервер не
          синхронизируются.
        </p>
      ) : null}
      {isReadSavedTab && !feedLoading && visibleItems.length === 0 && !feedError ? (
        <p className="muted">
          Здесь появятся прочитанные новости — после пролистывания ленты, свайпа вправо или дочитывания статьи. Хранятся 30 дней на этом
          устройстве.
        </p>
      ) : null}

      {!feedBlocking ? (
        <TikTokFeed
          hasMore={hasMore}
          items={visibleItems}
          key={`${feedFilter}-${feedPeriod}-${feedVisibilityRevision}`}
          loadingMore={loadingMore}
          onLoadMore={loadMore}
          swipeToRead={swipeToRead}
          scrollToRead={scrollToRead}
        />
      ) : null}
    </section>
  );
}
