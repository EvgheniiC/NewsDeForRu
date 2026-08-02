const DEFAULT_PUBLIC_APP_BASE_URL: string = "https://simplenewsapp.de";

export type ShareChannel = "whatsapp" | "telegram";

export function getPublicAppBaseUrl(): string {
  const raw: string | undefined = import.meta.env.VITE_PUBLIC_APP_BASE_URL?.trim();
  if (raw !== undefined && raw.length > 0) {
    return raw.replace(/\/$/, "");
  }
  return DEFAULT_PUBLIC_APP_BASE_URL;
}

export function buildNewsShareUrl(newsId: number): string {
  return `${getPublicAppBaseUrl()}/news/${newsId}`;
}

/** Title + summary + deep link line for WhatsApp (full message in one text field). */
export function buildNewsShareText(
  titleRu: string,
  oneSentenceSummary: string,
  shareUrl: string,
  sourceName: string = "",
  sourceUrl: string = ""
): string {
  const parts: string[] = [];
  const title: string = titleRu.trim();
  const summary: string = oneSentenceSummary.trim();
  if (title.length > 0) {
    parts.push(title);
  }
  if (summary.length > 0) {
    parts.push(summary);
  }
  if (sourceName.trim() || sourceUrl.trim()) {
    parts.push(`Источник: ${sourceName.trim() || "оригинал"}${sourceUrl.trim() ? ` — ${sourceUrl.trim()}` : ""}`);
  }
  parts.push(`Читать в приложении: ${shareUrl}`);
  return parts.join("\n\n");
}

/** Caption for Telegram share (URL is passed separately). */
export function buildTelegramShareCaption(
  titleRu: string,
  oneSentenceSummary: string,
  sourceName: string = "",
  sourceUrl: string = ""
): string {
  const parts: string[] = [];
  const title: string = titleRu.trim();
  const summary: string = oneSentenceSummary.trim();
  if (title.length > 0) {
    parts.push(title);
  }
  if (summary.length > 0) {
    parts.push(summary);
  }
  if (sourceName.trim() || sourceUrl.trim()) {
    parts.push(`Источник: ${sourceName.trim() || "оригинал"}${sourceUrl.trim() ? ` — ${sourceUrl.trim()}` : ""}`);
  }
  return parts.join("\n\n");
}

export function buildWhatsAppShareUrl(fullText: string): string {
  return `https://wa.me/?text=${encodeURIComponent(fullText)}`;
}

export function buildTelegramShareUrl(shareUrl: string, caption: string): string {
  const params: URLSearchParams = new URLSearchParams({
    url: shareUrl,
    text: caption,
  });
  return `https://t.me/share/url?${params.toString()}`;
}

export function buildShareUrlForChannel(
  channel: ShareChannel,
  titleRu: string,
  oneSentenceSummary: string,
  newsId: number,
  sourceName: string = "",
  sourceUrl: string = ""
): string {
  const shareUrl: string = buildNewsShareUrl(newsId);
  if (channel === "whatsapp") {
    const text: string = buildNewsShareText(titleRu, oneSentenceSummary, shareUrl, sourceName, sourceUrl);
    return buildWhatsAppShareUrl(text);
  }
  const caption: string = buildTelegramShareCaption(titleRu, oneSentenceSummary, sourceName, sourceUrl);
  return buildTelegramShareUrl(shareUrl, caption);
}
