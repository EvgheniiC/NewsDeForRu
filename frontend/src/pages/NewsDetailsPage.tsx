import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getNews, getNewsImpact } from "../api/client";
import type { ProcessedNews, RoleImpact, UserRole } from "../types/news";

export function NewsDetailsPage(): JSX.Element {
  const params = useParams<{ id: string }>();
  const [news, setNews] = useState<ProcessedNews | null>(null);
  const [impact, setImpact] = useState<RoleImpact | null>(null);
  const [role, setRole] = useState<UserRole>("tenant");
  const newsId: number = Number(params.id);

  useEffect(() => {
    if (!Number.isFinite(newsId)) {
      return;
    }
    void getNews(newsId).then(setNews);
  }, [newsId]);

  useEffect(() => {
    if (!Number.isFinite(newsId)) {
      return;
    }
    void getNewsImpact(newsId, role).then(setImpact);
  }, [newsId, role]);

  if (news === null) {
    return <p>Загрузка деталей...</p>;
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
