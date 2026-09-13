import { formatHealthTime } from "../lib/pipelineUi";
import type { HealthResponse, PipelineRunResponse } from "../types/pipeline";

interface FeedDevPanelsProps {
  health: HealthResponse | null;
  healthError: string;
  lastManualRun: PipelineRunResponse | null;
  pipelineHttpError: string;
  pipelineNetworkError: string;
  pipelineOkMessage: string | null;
  pipelineRunning: boolean;
  onRefresh: () => void;
}

export function FeedDevPanels({
  health,
  healthError,
  lastManualRun,
  pipelineHttpError,
  pipelineNetworkError,
  pipelineOkMessage,
  pipelineRunning,
  onRefresh
}: FeedDevPanelsProps): JSX.Element {
  const healthStatus: string | null = health?.status ?? null;

  return (
    <details className="feed-dev-panels">
      <summary className="feed-dev-panels-summary">
        Сервер и pipeline
        {healthStatus !== null ? (
          <span className={healthStatus === "ok" ? "health-ok" : "health-warn"}>{healthStatus}</span>
        ) : null}
      </summary>
      <div className="feed-dev-panels-body">
        <div className="panel health-panel">
          <h2 className="panel-title">Состояние сервера</h2>
          {healthError ? <p className="error">{healthError}</p> : null}
          {health ? (
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
                {health.last_pipeline_ok === null ? "—" : health.last_pipeline_ok ? "да" : "нет"}
              </li>
              <li>
                <span className="health-label">Run ID последнего прогона:</span>{" "}
                <code className="health-code">{health.last_pipeline_run_id ?? "—"}</code>
              </li>
              <li>
                <span className="health-label">Планировщик:</span> {health.pipeline_scheduler}
              </li>
            </ul>
          ) : null}
          {!health && !healthError ? <p className="muted">Загрузка…</p> : null}
        </div>

        <div className="panel pipeline-panel">
          <h2 className="panel-title">Последний ручной запуск pipeline</h2>
          <button disabled={pipelineRunning} onClick={onRefresh} type="button">
            {pipelineRunning ? "Выполняется pipeline…" : "Обновить через pipeline"}
          </button>
          {pipelineNetworkError ? <p className="error">Ошибка сети: {pipelineNetworkError}</p> : null}
          {pipelineHttpError ? <p className="error">Ошибка HTTP: {pipelineHttpError}</p> : null}
          {lastManualRun === null && !pipelineNetworkError && !pipelineHttpError && !pipelineRunning ? (
            <p className="muted">Ещё не запускали с этой страницы.</p>
          ) : null}
          {pipelineRunning ? <p className="loading-inline">Выполняется POST /pipeline/run…</p> : null}
          {pipelineOkMessage ? <p className="error">{pipelineOkMessage}</p> : null}
          {lastManualRun !== null ? (
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
          ) : null}
        </div>
      </div>
    </details>
  );
}
