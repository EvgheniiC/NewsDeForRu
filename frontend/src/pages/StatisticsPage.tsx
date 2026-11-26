import { useCallback, useEffect, useRef, useState, type ChangeEvent, type MutableRefObject } from "react";
import { useNavigate } from "react-router-dom";
import {
  ApiError,
  getModerationDailyStats,
  type ModerationDailyStats,
} from "../api/client";
import { useAuth } from "../context/AuthContext";
import { berlinTodayYmd } from "../lib/dateTimeBerlin";

function formatCount(loading: boolean, value: number | null): string {
  if (loading) {
    return "…";
  }
  if (value === null) {
    return "—";
  }
  return String(value);
}

function unspecifiedVisitCount(total: number | null, site: number | null, app: number | null): number {
  if (total === null || site === null || app === null) {
    return 0;
  }
  const remainder: number = total - site - app;
  return remainder > 0 ? remainder : 0;
}

export function StatisticsPage(): JSX.Element {
  const navigate = useNavigate();
  const { user, withModerationAccess, logout } = useAuth();
  const [statsDate, setStatsDate] = useState<string>(() => berlinTodayYmd());
  const [publishedCount, setPublishedCount] = useState<number | null>(null);
  const [moderationCount, setModerationCount] = useState<number | null>(null);
  const [visitCount, setVisitCount] = useState<number | null>(null);
  const [siteVisitCount, setSiteVisitCount] = useState<number | null>(null);
  const [appVisitCount, setAppVisitCount] = useState<number | null>(null);
  const [downloadCount, setDownloadCount] = useState<number | null>(null);
  const [statsLoading, setStatsLoading] = useState<boolean>(true);
  const [statsError, setStatsError] = useState<string>("");
  const todayYmd: string = berlinTodayYmd();
  const olderVisitCount: number = unspecifiedVisitCount(visitCount, siteVisitCount, appVisitCount);
  const statsRequestIdRef: MutableRefObject<number> = useRef<number>(0);

  const loadDailyStats = useCallback(
    async (day: string): Promise<void> => {
      const requestId: number = statsRequestIdRef.current + 1;
      statsRequestIdRef.current = requestId;
      setStatsLoading(true);
      try {
        const stats: ModerationDailyStats = await withModerationAccess(async (token: string) =>
          getModerationDailyStats(token, day),
        );
        if (statsRequestIdRef.current !== requestId) {
          return;
        }
        setPublishedCount(stats.published_count);
        setModerationCount(stats.moderation_count);
        setVisitCount(stats.visit_count);
        setSiteVisitCount(
          typeof stats.site_visit_count === "number" ? stats.site_visit_count : null,
        );
        setAppVisitCount(
          typeof stats.app_visit_count === "number" ? stats.app_visit_count : null,
        );
        setDownloadCount(typeof stats.download_count === "number" ? stats.download_count : null);
        setStatsError("");
      } catch (fetchError: unknown) {
        if (statsRequestIdRef.current !== requestId) {
          return;
        }
        if (fetchError instanceof ApiError && fetchError.status === 401) {
          await logout();
          navigate("/login", { replace: true, state: { from: "/statistics" } });
          return;
        }
        if (fetchError instanceof ApiError && fetchError.status === 404) {
          setPublishedCount(null);
          setModerationCount(null);
          setVisitCount(null);
          setSiteVisitCount(null);
          setAppVisitCount(null);
          setDownloadCount(null);
          setStatsError("Сервер ещё не отдаёт статистику. Обновите backend и перезапустите его.");
          return;
        }
        setPublishedCount(null);
        setModerationCount(null);
        setVisitCount(null);
        setSiteVisitCount(null);
        setAppVisitCount(null);
        setDownloadCount(null);
        setStatsError(
          fetchError instanceof Error ? fetchError.message : "Не удалось загрузить статистику.",
        );
      } finally {
        if (statsRequestIdRef.current === requestId) {
          setStatsLoading(false);
        }
      }
    },
    [logout, navigate, withModerationAccess],
  );

  useEffect(() => {
    if (!user?.can_moderate) {
      return;
    }
    void loadDailyStats(statsDate);
  }, [loadDailyStats, statsDate, user?.can_moderate]);

  return (
    <section>
      <h1>Статистика</h1>
      {statsError !== "" && <p className="error">{statsError}</p>}
      <section className="moderation-daily-stats" aria-label="Скачивания приложения">
        <h2 className="moderation-daily-stats-title">Приложение</h2>
        <div className="moderation-daily-stats-grid moderation-daily-stats-grid-single">
          <article className="moderation-daily-stats-card">
            <p className="moderation-daily-stats-value">{formatCount(statsLoading, downloadCount)}</p>
            <p className="moderation-daily-stats-label">Скачивания</p>
            <p className="moderation-daily-stats-hint">
              Сколько человек установили Android-приложение: первое открытие после согласия на статистику.
              Повторный запуск не увеличивает число. От выбранной даты не зависит.
            </p>
          </article>
        </div>
      </section>
      <section className="moderation-daily-stats" aria-label="Счётчики за день">
        <div className="moderation-daily-stats-head">
          <div>
            <h2 className="moderation-daily-stats-title">За день</h2>
            <p className="moderation-daily-stats-hint">Календарный день по берлинскому времени.</p>
          </div>
          <label className="moderation-daily-stats-date">
            Дата
            <input
              max={todayYmd}
              onChange={(event: ChangeEvent<HTMLInputElement>) => {
                const nextDay: string = event.target.value;
                if (nextDay === "") {
                  return;
                }
                setStatsDate(nextDay);
              }}
              type="date"
              value={statsDate}
            />
          </label>
        </div>
        <div className="moderation-daily-stats-grid">
          <article className="moderation-daily-stats-card">
            <p className="moderation-daily-stats-value">{formatCount(statsLoading, publishedCount)}</p>
            <p className="moderation-daily-stats-label">В ленте</p>
            <p className="moderation-daily-stats-hint">
              Опубликованы в этот день, любая тема и любой источник.
            </p>
          </article>
          <article className="moderation-daily-stats-card">
            <p className="moderation-daily-stats-value">{formatCount(statsLoading, moderationCount)}</p>
            <p className="moderation-daily-stats-label">На модерации</p>
            <p className="moderation-daily-stats-hint">
              Отправлены на модерацию в этот день, даже если их потом опубликовали или отклонили.
            </p>
          </article>
          <article className="moderation-daily-stats-card">
            <p className="moderation-daily-stats-value">{formatCount(statsLoading, siteVisitCount)}</p>
            <p className="moderation-daily-stats-label">Посещения сайта</p>
            <p className="moderation-daily-stats-hint">
              Одно открытие сайта на сессию. Учитываются только посетители, которые согласились на
              статистику.
            </p>
          </article>
          <article className="moderation-daily-stats-card">
            <p className="moderation-daily-stats-value">{formatCount(statsLoading, appVisitCount)}</p>
            <p className="moderation-daily-stats-label">Посещения приложения</p>
            <p className="moderation-daily-stats-hint">
              Одно открытие Android-приложения на сессию. Учитываются только посетители, которые
              согласились на статистику.
            </p>
          </article>
        </div>
        {!statsLoading && olderVisitCount > 0 && (
          <p className="moderation-daily-stats-hint">
            Ещё {olderVisitCount} посещений записаны до разделения сайта и приложения и не входят в
            эти две цифры.
          </p>
        )}
      </section>
    </section>
  );
}
