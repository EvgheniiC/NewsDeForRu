import { useState } from "react";
import { Capacitor } from "@capacitor/core";
import { enqueueOne } from "../analytics/engagementQueue";
import { ApiError, getNewsFullArticle } from "../api/client";

function splitArticleParagraphs(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((p: string) => p.trim())
    .filter((p: string) => p.length > 0);
}

interface FullArticleMobileSectionProps {
  newsId: number;
}

export function FullArticleMobileSection({ newsId }: FullArticleMobileSectionProps): JSX.Element | null {
  if (!Capacitor.isNativePlatform()) {
    return null;
  }

  const [fullText, setFullText] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const handleLoadFullArticle = (): void => {
    if (loading || fullText !== null) {
      return;
    }
    setLoading(true);
    setError("");
    void getNewsFullArticle(newsId)
      .then((res) => {
        setFullText(res.full_article_ru);
        enqueueOne(newsId, "expand_full_article", { cached: res.cached }, true);
      })
      .catch((err: unknown) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError(err instanceof Error ? err.message : "Не удалось загрузить полный текст.");
        }
      })
      .finally(() => {
        setLoading(false);
      });
  };

  return (
    <section aria-labelledby="full-article-heading" className="news-full-article">
      {fullText === null ? (
        <button
          className="news-full-article__button"
          disabled={loading}
          onClick={handleLoadFullArticle}
          type="button"
        >
          {loading ? "Загрузка…" : "Читать статью целиком"}
        </button>
      ) : null}
      {error ? <p className="error news-full-article__error">{error}</p> : null}
      {fullText !== null ? (
        <>
          <h2 className="news-full-article__title" id="full-article-heading">
            Статья целиком
          </h2>
          <div className="news-full-article__body">
            {splitArticleParagraphs(fullText).map((paragraph: string, index: number) => (
              <p className="news-full-article__paragraph" key={index}>
                {paragraph}
              </p>
            ))}
          </div>
        </>
      ) : null}
    </section>
  );
}
