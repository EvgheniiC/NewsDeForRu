import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Capacitor } from "@capacitor/core";
import { CompactSelect } from "../components/CompactSelect";
import { TikTokFeed } from "../components/TikTokFeed";
import { useInfiniteFeed } from "../hooks/useInfiniteFeed";
import { useReadSavedFeed } from "../hooks/useReadSavedFeed";
import { useUsefulSavedFeed } from "../hooks/useUsefulSavedFeed";
import { useAuth } from "../context/AuthContext";
import { filterActiveFeedItems, isFeedCaughtUp } from "../lib/feedVisibility";
import { feedFilterPillClass } from "../lib/newsUi";
import { READ_STATE_CHANGED_EVENT } from "../lib/readStateStorage";
import { flushPendingScrollRead, isWebScrollToReadEnabled } from "../lib/scrollToRead";
import { USEFUL_STORAGE_CHANGED_EVENT } from "../lib/usefulStorage";
import type { FeedFilterKey, FeedPeriodKey } from "../types/news";

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
  const { user } = useAuth();
  const feedLocationState = location.state as FeedLocationState | null | undefined;
  const verificationPendingEmail: string = feedLocationState?.verificationPendingEmail?.trim() ?? "";
  const devVerificationLink: string | null =
    typeof feedLocationState?.devVerificationLink === "string" && feedLocationState.devVerificationLink.length > 0
      ? feedLocationState.devVerificationLink
      : null;
  const [feedFilter, setFeedFilter] = useState<FeedFilterKey>("life");
  const [feedPeriod, setFeedPeriod] = useState<FeedPeriodKey>("all");
  /** Bumped on read/useful storage changes so visibleItems re-filters; must not be in TikTokFeed key. */
  const [, setFeedVisibilityRevision] = useState<number>(0);

  const isSavedUsefulTab: boolean = feedFilter === "saved_useful";
  const isReadSavedTab: boolean = feedFilter === "read_saved";
  const isArchiveTab: boolean = isSavedUsefulTab || isReadSavedTab;
  /** Placeholder topic when archive tabs disable infinite scrolling; no requests are sent (`enabled: false`). */
  const infiniteFeedFilter: Exclude<FeedFilterKey, "saved_useful" | "read_saved"> =
    isArchiveTab ? "life" : feedFilter;

  const { items: infiniteItems, loading: infiniteLoading, loadingMore, feedError: infiniteFeedError, nextCursor, loadMore } =
    useInfiniteFeed(infiniteFeedFilter, feedPeriod, { enabled: !isArchiveTab });

  const {
    items: savedItems,
    loading: savedLoading,
    feedError: savedFeedError
  } = useUsefulSavedFeed(isSavedUsefulTab);

  const {
    items: readItems,
    loading: readLoading,
    feedError: readFeedError
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
  const feedCaughtUp: boolean =
    !isArchiveTab && !feedLoading && !feedError && isFeedCaughtUp(infiniteItems, feedFilter);
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

  const dismissVerificationNotice = (): void => {
    navigate(location.pathname, { replace: true, state: null });
  };

  return (
    <section className="feed-page">
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

      {feedFilter === "positive" ? (
        <h2 className="feed-section-heading feed-section-heading--positive">☀️ Только Позитивные Новости (ТПН)</h2>
      ) : null}

      {feedLoading && visibleItems.length === 0 && infiniteItems.length === 0 && (
        <p className="loading-inline">Загрузка ленты…</p>
      )}
      {feedError && <p className="error">{feedError}</p>}
      {feedCaughtUp ? (
        <div className="feed-empty-state">
          <p>Всё прочитано. Ждите новых новостей.</p>
          <p className="muted">
            Лента обновляется автоматически. Открытые статьи тоже попадают в «Прочитанные».{" "}
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
      {!feedLoading && !feedError && !isArchiveTab && !feedCaughtUp && visibleItems.length === 0 ? (
        <div className="feed-empty-state">
          <p>Пока нет новостей в этой подборке.</p>
          <p className="muted">Лента обновляется автоматически.</p>
        </div>
      ) : null}
      {isSavedUsefulTab && !feedLoading && visibleItems.length === 0 && !feedError ? (
        <p className="muted">
          {user !== null
            ? "Здесь появятся новости, отмеченные «Полезно». Хранятся 60 дней и синхронизируются с аккаунтом."
            : "Здесь появятся новости, отмеченные «Полезно». Хранятся 60 дней на этом устройстве. Войдите в аккаунт, чтобы не потерять их при смене телефона."}
        </p>
      ) : null}
      {isReadSavedTab && !feedLoading && visibleItems.length === 0 && !feedError ? (
        <p className="muted">
          {user !== null
            ? "Здесь появятся прочитанные новости — после пролистывания ленты, свайпа вправо или дочитывания статьи. Хранятся 30 дней и синхронизируются с аккаунтом."
            : "Здесь появятся прочитанные новости — после пролистывания ленты, свайпа вправо или дочитывания статьи. Хранятся 30 дней на этом устройстве. Войдите в аккаунт, чтобы не потерять их при смене телефона."}
        </p>
      ) : null}

      {!feedBlocking ? (
        <TikTokFeed
          hasMore={hasMore}
          items={visibleItems}
          key={`${feedFilter}-${feedPeriod}`}
          loadingMore={loadingMore}
          onLoadMore={loadMore}
          stackedLayout={isArchiveTab}
          swipeToRead={swipeToRead}
          scrollToRead={scrollToRead}
        />
      ) : null}
    </section>
  );
}
