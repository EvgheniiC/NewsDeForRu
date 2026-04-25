import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError, getNews, getNewsImpact } from "../api/client";
import type { ProcessedNews, RoleImpact, UserRole } from "../types/news";

export function NewsDetailsPage(): JSX.Element {
  const params = useParams<{ id: string }>();
  const [news, setNews] = useState<ProcessedNews | null>(null);
  const [impact, setImpact] = useState<RoleImpact | null>(null);
  const [role, setRole] = useState<UserRole>("tenant");
  const [loadingNews, setLoadingNews] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string>("");
  const [notFound, setNotFound] = useState<boolean>(false);
  const [impactError, setImpactError] = useState<string>("");
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

  useEffect(() => {
    if (!Number.isFinite(newsId) || news === null) {
      return;
    }
    setImpactError("");
    void getNewsImpact(newsId, role)
      .then((data: RoleImpact) => {
        setImpact(data);
      })
      .catch((error: unknown) => {
        setImpact(null);
        setImpactError(
          error instanceof Error ? error.message : "Не удалось загрузить блок для роли.",
        );
      });
  }, [newsId, role, news]);

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
      <div className="role-selector">
        <label htmlFor="role">Роль:</label>
        <select id="role" onChange={(event) => setRole(event.target.value as UserRole)} value={role}>
          <option value="owner">Владелец</option>
          <option value="tenant">Арендатор</option>
          <option value="buyer">Покупатель</option>
        </select>
      </div>
      {impactError && <p className="error">{impactError}</p>}
      <p>
        <strong>Что это значит для тебя:</strong> {impact?.text ?? ""}
      </p>
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
