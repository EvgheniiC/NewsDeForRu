import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { enqueueOne } from "../analytics/engagementQueue";
import { ApiError, getNews } from "../api/client";
import { newsTopicLabelRu, type ImpactPresentation, type ProcessedNews } from "../types/news";

const READ_ARTICLE_RATIO: number = 0.91;

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
      <div className="news-perspective">
        <p className="news-perspective__text">{news.impact_owner}</p>
      </div>
      <div className="news-perspective">
        <p className="news-perspective__text">{news.impact_tenant}</p>
      </div>
      <div className="news-perspective">
        <p className="news-perspective__text">{news.impact_buyer}</p>
      </div>
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

  return (
    <section>
      <Link to="/">← Назад</Link>
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
      <p>
        <strong>Суть:</strong> {news.one_sentence_summary}
      </p>
      <p>
        <strong>Простым языком:</strong> {news.plain_language}
      </p>
      {renderImpactBlock(presentation, news)}
      <p>
        <strong>Что сделать:</strong> {news.action_items}
      </p>
      <p>
        <strong>Бонус:</strong> {news.bonus_block}
      </p>
      <p>
        <strong>Спойлер:</strong> {news.spoiler}
      </p>
      <p className="news-detail-category">
        Категория:{" "}
        <span className="news-topic-label">{newsTopicLabelRu(news.topic)}</span>
      </p>
      <a href={news.source_url} onClick={handleOpenSourceClick} rel="noreferrer" target="_blank">
        Оригинальный источник
      </a>
    </section>
  );
}
