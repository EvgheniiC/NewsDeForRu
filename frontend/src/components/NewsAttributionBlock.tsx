import { formatDateRuBerlin, formatDateTimeRuBerlin } from "../lib/dateTimeBerlin";
import type { SourceUrlStatus } from "../types/news";

interface NewsAttributionBlockProps {
  sourceName: string;
  sourceUrl: string;
  /** When unavailable, hide the publisher link and show a notice instead. */
  sourceUrlStatus?: SourceUrlStatus;
  publishedAt: string;
  originalTitle?: string | null;
  originalLanguage?: string | null;
  retrievedAt?: string | null;
  licence?: string | null;
  licenceUrl?: string | null;
  copyrightHolder?: string | null;
  changesNotice?: string | null;
  /** Compact cards show date only; detail pages show date and time. */
  variant?: "compact" | "detail";
  onSourceClick?: () => void;
}

export function NewsAttributionBlock({
  sourceName,
  sourceUrl,
  sourceUrlStatus = "unknown",
  publishedAt,
  originalTitle,
  originalLanguage,
  retrievedAt,
  licence,
  licenceUrl,
  copyrightHolder,
  changesNotice,
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
        <>
          {originalTitle ? (
            <p className="news-attribution__disclaimer">
              Оригинал{originalLanguage ? ` (${originalLanguage})` : ""}: {originalTitle}
            </p>
          ) : null}
          <p className="news-attribution__disclaimer">
            {changesNotice ??
              "Краткая сводка на русском языке, подготовленная автоматически. Это не оригинальный текст источника."}
          </p>
          {copyrightHolder ? (
            <p className="news-attribution__disclaimer">Правообладатель: {copyrightHolder}</p>
          ) : null}
          {licence ? (
            <p className="news-attribution__disclaimer">
              Лицензия:{" "}
              {licenceUrl ? (
                <a href={licenceUrl} rel="noreferrer" target="_blank">
                  {licence}
                </a>
              ) : (
                licence
              )}
            </p>
          ) : null}
          {retrievedAt ? (
            <p className="news-attribution__disclaimer">
              Получено: <time dateTime={retrievedAt}>{formatDateTimeRuBerlin(retrievedAt)}</time>
            </p>
          ) : null}
        </>
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
