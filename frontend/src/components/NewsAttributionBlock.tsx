import { formatDateRuBerlin, formatDateTimeRuBerlin } from "../lib/dateTimeBerlin";
import type { SourceUrlStatus } from "../types/news";

interface NewsAttributionBlockProps {
  sourceName: string;
  sourceUrl: string;
  /** When unavailable, hide the publisher link and show a notice instead. */
  sourceUrlStatus?: SourceUrlStatus;
  publishedAt: string;
  /** Compact cards show date only; detail pages show date and time. */
  variant?: "compact" | "detail";
  onSourceClick?: () => void;
}

export function NewsAttributionBlock({
  sourceName,
  sourceUrl,
  sourceUrlStatus = "unknown",
  publishedAt,
  variant = "detail",
  onSourceClick
}: NewsAttributionBlockProps): JSX.Element {
  const publishedLabel: string =
    variant === "compact" ? formatDateRuBerlin(publishedAt) : formatDateTimeRuBerlin(publishedAt);
  const sourceUnavailable: boolean = sourceUrlStatus === "unavailable";

  return (
    <div className={`news-attribution news-attribution--${variant}`}>
      <p className="news-attribution__meta">
        <span className="news-attribution__label">Источник:</span>{" "}
        <span className="news-attribution__source">{sourceName}</span>
        <span aria-hidden="true" className="news-attribution__sep">
          {" "}
          ·{" "}
        </span>
        <span className="news-attribution__label">Опубликовано:</span>{" "}
        <time dateTime={publishedAt}>{publishedLabel}</time>
      </p>
      {variant === "detail" ? (
        <p className="news-attribution__disclaimer">
          Краткая сводка на русском языке, подготовленная автоматически. Это не оригинальный текст
          издания.
        </p>
      ) : null}
      {sourceUnavailable ? (
        <p className="news-attribution__source-gone" role="status">
          Оригинальная публикация была удалена или больше недоступна на сайте издателя.
        </p>
      ) : (
        <a
          className="news-attribution__link"
          href={sourceUrl}
          onClick={onSourceClick}
          rel="noreferrer"
          target="_blank"
        >
          Оригинальная статья на сайте издателя
        </a>
      )}
    </div>
  );
}
