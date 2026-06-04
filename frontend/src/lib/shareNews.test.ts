import { describe, expect, it } from "vitest";
import {
  buildNewsShareText,
  buildNewsShareUrl,
  buildShareUrlForChannel,
  buildTelegramShareCaption,
  buildWhatsAppShareUrl,
} from "./shareNews";

describe("shareNews", () => {
  it("buildNewsShareUrl uses default public base", () => {
    expect(buildNewsShareUrl(42)).toBe("https://simplenewsapp.de/news/42");
  });

  it("buildNewsShareText combines title, summary and link", () => {
    const text: string = buildNewsShareText(
      "Заголовок",
      "Краткая суть",
      "https://simplenewsapp.de/news/7",
    );
    expect(text).toContain("Заголовок");
    expect(text).toContain("Краткая суть");
    expect(text).toContain("Читать в приложении: https://simplenewsapp.de/news/7");
  });

  it("buildTelegramShareCaption omits link line", () => {
    expect(buildTelegramShareCaption("A", "B")).toBe("A\n\nB");
  });

  it("buildWhatsAppShareUrl encodes text", () => {
    expect(buildWhatsAppShareUrl("hello world")).toBe("https://wa.me/?text=hello%20world");
  });

  it("buildShareUrlForChannel returns WhatsApp link", () => {
    const url: string = buildShareUrlForChannel("whatsapp", "T", "S", 1);
    expect(url.startsWith("https://wa.me/?text=")).toBe(true);
    expect(decodeURIComponent(url)).toContain("T");
  });

  it("buildShareUrlForChannel returns Telegram link", () => {
    const url: string = buildShareUrlForChannel("telegram", "T", "S", 5);
    expect(url.startsWith("https://t.me/share/url?")).toBe(true);
    expect(url).toContain("url=");
    expect(url).toContain("text=");
  });
});
