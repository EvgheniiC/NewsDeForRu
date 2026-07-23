import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { enqueueOne } from "../analytics/engagementQueue";
import { ApiError, getNews } from "../api/client";
import { markNewsAsRead } from "../lib/readStateStorage";
import { NewsArticleBody } from "../components/NewsArticleBody";
import { newsTopicChipClass } from "../lib/newsUi";
import { newsTopicLabelRu, type ProcessedNews } from "../types/news";

const READ_ARTICLE_RATIO: number = 0.91;

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
        <p className="error">{loadError}</p>
      </section>
    );
  }

  if (notFound || news === null) {
    return (
      <section>
        <p>Новость не найдена.</p>
      </section>
    );
  }

  return (
    <section>
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
        <NewsArticleBody news={news} />
      </article>
      <p className="news-detail-category">
        Категория: <span className={newsTopicChipClass(news.topic)}>{newsTopicLabelRu(news.topic)}</span>
      </p>
    </section>
  );
}
