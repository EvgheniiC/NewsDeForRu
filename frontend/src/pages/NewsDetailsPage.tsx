import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, getNews } from "../api/client";
import type { ImpactPresentation, ProcessedNews } from "../types/news";

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
  const newsId: number = Number(params.id);

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

  return (
    <section>
      <Link to="/">← Назад</Link>
      <h1>{news.title}</h1>
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
      <a href={news.source_url} rel="noreferrer" target="_blank">
        Оригинальный источник
      </a>
    </section>
  );
}
