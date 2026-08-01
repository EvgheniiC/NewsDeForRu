import { enqueueOne } from "../analytics/engagementQueue";
import {
  IMPACT_PERSPECTIVE_LABELS,
  type ImpactPresentation,
  type ProcessedNews
} from "../types/news";
// Temporarily disabled: full-article fetch may be unlawful in Germany (Urheberrecht).
// import { FullArticleMobileSection } from "./FullArticleMobileSection";
import { NewsAttributionBlock } from "./NewsAttributionBlock";
import { ShareNewsMobileSection } from "./ShareNewsMobileSection";

const IMPACT_PERSPECTIVE_MODIFIERS: readonly string[] = [
  "news-perspective--owner",
  "news-perspective--tenant",
  "news-perspective--buyer"
] as const;

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
  headingIdPrefix: string
): JSX.Element | null {
  if (presentation === "none") {
    return null;
  }
  if (presentation === "single") {
    const headingId: string = `${headingIdPrefix}-impact-single`;
    return (
      <section aria-labelledby={headingId} className="news-perspectives">
        <h2 className="news-perspectives__title" id={headingId}>
          Что это значит
        </h2>
        <div className="news-perspective">
          <p className="news-perspective__text">{news.impact_unified ?? ""}</p>
        </div>
      </section>
    );
  }
  const headingId: string = `${headingIdPrefix}-perspectives`;
  return (
    <section aria-labelledby={headingId} className="news-perspectives">
      <h2 className="news-perspectives__title" id={headingId}>
        Что это значит с разных сторон
      </h2>
      {[news.impact_owner, news.impact_tenant, news.impact_buyer].map(
        (text: string, index: number) => (
          <div
            key={IMPACT_PERSPECTIVE_MODIFIERS[index]}
            className={`news-perspective ${IMPACT_PERSPECTIVE_MODIFIERS[index]}`}
          >
            <p className="news-perspective__label">{IMPACT_PERSPECTIVE_LABELS[index]}</p>
            <p className="news-perspective__text">{text}</p>
          </div>
        )
      )}
    </section>
  );
}

interface NewsArticleBodyProps {
  news: ProcessedNews;
  /** Prefix for heading ids so multiple expanded cards stay unique. */
  headingIdPrefix?: string;
  /** When false, skip share / full-article mobile sections (e.g. tests). Default true. */
  includeMobileExtras?: boolean;
}

/** Editorial body shared by the detail page and in-feed expand. */
export function NewsArticleBody({
  news,
  headingIdPrefix = `news-${news.id}`,
  includeMobileExtras = true
}: NewsArticleBodyProps): JSX.Element {
  const presentation: ImpactPresentation = news.impact_presentation ?? "multi";
  const additionalText: string | null = formatAdditionalBlock(news.bonus_block, news.spoiler);

  const handleOpenSourceClick = (): void => {
    enqueueOne(news.id, "open_source", {}, true);
  };

  return (
    <>
      <p className="news-detail-lead">
        <strong>Суть:</strong> {news.one_sentence_summary}
      </p>
      <p className="news-detail-body">
        <strong>Простым языком:</strong> {news.plain_language}
      </p>
      {renderImpactBlock(presentation, news, headingIdPrefix)}
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
        sourceUrlStatus={news.source_url_status ?? "unknown"}
        variant="detail"
      />
      {includeMobileExtras ? (
        <>
          <ShareNewsMobileSection
            newsId={news.id}
            oneSentenceSummary={news.one_sentence_summary}
            titleRu={news.title}
          />
          {/* Temporarily disabled: full-article fetch may be unlawful in Germany (Urheberrecht).
          <FullArticleMobileSection newsId={news.id} />
          */}
        </>
      ) : null}
    </>
  );
}
