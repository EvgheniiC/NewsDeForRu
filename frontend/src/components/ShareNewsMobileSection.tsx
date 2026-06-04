import { Capacitor } from "@capacitor/core";
import { enqueueOne } from "../analytics/engagementQueue";
import { buildShareUrlForChannel, type ShareChannel } from "../lib/shareNews";

interface ShareNewsMobileSectionProps {
  newsId: number;
  titleRu: string;
  oneSentenceSummary: string;
}

export function ShareNewsMobileSection({
  newsId,
  titleRu,
  oneSentenceSummary,
}: ShareNewsMobileSectionProps): JSX.Element | null {
  if (!Capacitor.isNativePlatform()) {
    return null;
  }

  const handleShareClick = (channel: ShareChannel): void => {
    enqueueOne(newsId, "share", { channel }, true);
  };

  const whatsAppHref: string = buildShareUrlForChannel("whatsapp", titleRu, oneSentenceSummary, newsId);
  const telegramHref: string = buildShareUrlForChannel("telegram", titleRu, oneSentenceSummary, newsId);

  return (
    <section aria-labelledby="share-news-heading" className="news-share">
      <h2 className="news-share__title" id="share-news-heading">
        Поделиться
      </h2>
      <div className="news-share__actions">
        <a
          className="news-share__button news-share__button--whatsapp"
          href={whatsAppHref}
          onClick={() => {
            handleShareClick("whatsapp");
          }}
          rel="noopener noreferrer"
          target="_blank"
        >
          WhatsApp
        </a>
        <a
          className="news-share__button news-share__button--telegram"
          href={telegramHref}
          onClick={() => {
            handleShareClick("telegram");
          }}
          rel="noopener noreferrer"
          target="_blank"
        >
          Telegram
        </a>
      </div>
    </section>
  );
}
