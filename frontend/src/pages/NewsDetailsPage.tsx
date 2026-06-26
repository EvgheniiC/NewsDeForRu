import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { enqueueOne } from "../analytics/engagementQueue";
import { ApiError, getNews } from "../api/client";
import { markNewsAsRead } from "../lib/readStateStorage";
import { FullArticleMobileSection } from "../components/FullArticleMobileSection";
import { NewsAttributionBlock } from "../components/NewsAttributionBlock";
import { ShareNewsMobileSection } from "../components/ShareNewsMobileSection";
import { newsTopicChipClass } from "../lib/newsUi";
import {
  IMPACT_PERSPECTIVE_LABELS,
  newsTopicLabelRu,
  type ImpactPresentation,
  type ProcessedNews
} from "../types/news";

const IMPACT_PERSPECTIVE_MODIFIERS: readonly string[] = [
  "news-perspective--owner",
  "news-perspective--tenant",
  "news-perspective--buyer"
] as const;

const READ_ARTICLE_RATIO: number = 0.91;

/** Legacy API placeholders (no longer stored for new items); treat as absent. */
const LEGACY_EMPTY_BONUS: string =
  "Дополнительного редакционного блока не передано.";
const LEGACY_EMPTY_SPOILER: string =
  "Отдельной «интриги» нет — главное изложено в тексте выше.";

function normalizeEditorialExtra(raw: string, legacyPlaceholder: string): string {
  const t: string = raw.trim();
  if (t === "" || t === legacyPlaceholder) {
    return "";
  }
  return t;
}

/** One additional-details line; identical bonus and spoiler strings are de-duplicated. */
function formatAdditionalBlock(bonusBlock: string, spoiler: string): string | null {
  const bonus: string = normalizeEditorialExtra(bonusBlock, LEGACY_EMPTY_BONUS);
  const sp: string = normalizeEditorialExtra(spoiler, LEGACY_EMPTY_SPOILER);
  if (bonus === "" && sp === "") {
    return null;
  }
  if (bonus === sp) {
    return bonus;
  }
  const parts: string[] = [];
  if (bonus !== "") {
    parts.push(bonus);
  }
  if (sp !== "") {
    parts.push(sp);
  }
  return parts.join(" ");
}

function renderImpactBlock(
  presentation: ImpactPresentation,
  news: ProcessedNews,
): JSX.Element | null {
  if (presentation === "none") {
    return null;
  }
  if (presentation === "single") {
    return (
      <section aria-labelledby="impact-single-heading" className="news-perspectives">
        <h2 className="news-perspectives__title" id="impact-single-heading">
          Что это значит
        </h2>
        <div className="news-perspective">
          <p className="news-perspective__text">{news.impact_unified ?? ""}</p>
        </div>
      </section>
    );
  }
  return (
    <section aria-labelledby="perspectives-heading" className="news-perspectives">
      <h2 className="news-perspectives__title" id="perspectives-heading">
        Что это значит с разных сторон
      </h2>
      {[
        news.impact_owner,
        news.impact_tenant,
        news.impact_buyer
      ].map((text: string, index: number) => (
        <div
          key={IMPACT_PERSPECTIVE_MODIFIERS[index]}
          className={`news-perspective ${IMPACT_PERSPECTIVE_MODIFIERS[index]}`}
        >
          <p className="news-perspective__label">{IMPACT_PERSPECTIVE_LABELS[index]}</p>
          <p className="news-perspective__text">{text}</p>
        </div>
      ))}
    </section>
  );
}

export function NewsDetailsPage(): JSX.Element {
  const params = useParams<{ id: string }>();
  const [news, setNews] = useState<ProcessedNews | null>(null);
  const [loadingNews, setLoadingNews] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string>("");
  const [notFound, setNotFound] = useState<boolean>(false);
  const readArticleSentRef: { current: boolean } = useRef<boolean>(false);
  const newsId: number = Number(params.id);

  useEffect(() => {
    readArticleSentRef.current = false;
  }, [newsId]);

  useEffect(() => {
    if (!Number.isFinite(newsId)) {
      setLoadingNews(false);
      setLoadError("Некорректный идентификатор новости.");
      setNotFound(false);
      setNews(null);
      return;
    }
    setLoadingNews(true);
    setLoadError("");
    setNotFound(false);
    void getNews(newsId)
      .then((data: ProcessedNews) => {
        setNews(data);
      })
      .catch((error: unknown) => {
        setNews(null);
        if (error instanceof ApiError && error.status === 404) {
          setNotFound(true);
        } else {
          setLoadError(error instanceof Error ? error.message : "Не удалось загрузить новость.");
        }
      })
      .finally(() => {
        setLoadingNews(false);
      });
  }, [newsId]);

  useEffect(() => {
    if (news === null) {
      return;
    }
    let shortPageTimerId: ReturnType<typeof window.setTimeout> | undefined;

    const onScroll = (): void => {
      if (readArticleSentRef.current) {
        return;
      }
      const el: HTMLElement = document.documentElement;
      const scrollRoom: number = el.scrollHeight - el.clientHeight;
      if (scrollRoom <= 8) {
        return;
      }
      const ratio: number = el.scrollTop / scrollRoom;
      if (ratio >= READ_ARTICLE_RATIO) {
        readArticleSentRef.current = true;
        markNewsAsRead(newsId);
        enqueueOne(newsId, "read_complete_article", { max_ratio: Math.min(1, ratio) }, true);
      }
    };

    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();

    const checkShortPage = (): void => {
      if (readArticleSentRef.current || shortPageTimerId !== undefined) {
        return;
      }
      const el: HTMLElement = document.documentElement;
      if (el.scrollHeight > el.clientHeight + 40) {
        return;
      }
      shortPageTimerId = window.setTimeout(() => {
        if (!readArticleSentRef.current && document.visibilityState === "visible") {
          readArticleSentRef.current = true;
          markNewsAsRead(newsId);
          enqueueOne(newsId, "read_complete_article", { max_ratio: 1 }, true);
        }
      }, 3200);
    };
    window.requestAnimationFrame(() => {
      checkShortPage();
    });

    return (): void => {
      if (shortPageTimerId !== undefined) {
        window.clearTimeout(shortPageTimerId);
      }
      window.removeEventListener("scroll", onScroll);
    };
  }, [news, newsId]);

  if (loadingNews) {
    return <p>Загрузка деталей...</p>;
  }

  if (loadError) {
    return (
      <section>
        <Link to="/">← Назад</Link>
        <p className="error">{loadError}</p>
      </section>
    );
  }

  if (notFound || news === null) {
    return (
      <section>
        <Link to="/">← Назад</Link>
        <p>Новость не найдена.</p>
      </section>
    );
  }

  const presentation: ImpactPresentation = news.impact_presentation ?? "multi";

  const handleOpenSourceClick = (): void => {
    enqueueOne(newsId, "open_source", {}, true);
  };

  const additionalText: string | null = formatAdditionalBlock(
    news.bonus_block,
    news.spoiler,
  );

  return (
    <section>
      <Link to="/">← Назад</Link>
      <article className="news-detail-article">
        {news.is_urgent || news.is_positive ? (
          <div className="news-card-badges">
            {news.is_urgent ? <span className="news-badge news-badge--urgent">Срочно</span> : null}
            {news.is_positive ? <span className="news-badge news-badge--positive">Хорошая новость</span> : null}
          </div>
        ) : null}
        <h1>{news.title}</h1>
        {news.image_url ? (
          <img
            alt={news.title}
            className="news-detail-image"
            decoding="async"
            loading="lazy"
            src={news.image_url}
          />
        ) : null}
        <p className="news-detail-lead">
          <strong>Суть:</strong> {news.one_sentence_summary}
        </p>
        <p className="news-detail-body">
          <strong>Простым языком:</strong> {news.plain_language}
        </p>
        {renderImpactBlock(presentation, news)}
        {news.action_items.trim().length > 0 ? (
          <p className="news-detail-body">
            <strong>Что сделать:</strong> {news.action_items}
          </p>
        ) : null}
        {additionalText !== null ? (
          <p className="news-detail-body">
            <strong>Дополнительно:</strong> {additionalText}
          </p>
        ) : null}
        <NewsAttributionBlock
          onSourceClick={handleOpenSourceClick}
          publishedAt={news.published_at}
          sourceName={news.source_name}
          sourceUrl={news.source_url}
          variant="detail"
        />
      </article>
      <ShareNewsMobileSection
        newsId={newsId}
        oneSentenceSummary={news.one_sentence_summary}
        titleRu={news.title}
      />
      <FullArticleMobileSection newsId={newsId} />
      <p className="news-detail-category">
        Категория: <span className={newsTopicChipClass(news.topic)}>{newsTopicLabelRu(news.topic)}</span>
      </p>
    </section>
  );
}
