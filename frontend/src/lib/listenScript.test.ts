import { describe, expect, test } from "vitest";
import { buildListenChunks, splitSpeechText } from "./listenScript";

describe("splitSpeechText", () => {
  test("splits long text on sentence boundaries", () => {
    const chunks: string[] = splitSpeechText("Первое предложение. Второе предложение длиннее.", 24);
    expect(chunks.length).toBeGreaterThan(1);
    expect(chunks.join(" ")).toContain("Первое");
    expect(chunks.every((chunk: string) => chunk.length <= 24)).toBe(true);
  });

  test("returns an empty list for blank text", () => {
    expect(splitSpeechText("   ")).toEqual([]);
  });
});

describe("buildListenChunks", () => {
  test("speaks the preview without the article extras", () => {
    const chunks: string[] = buildListenChunks({
      title: "Заголовок",
      subtitle: "Суть новости",
    });
    expect(chunks.join(" ")).toBe("Заголовок Суть новости");
  });

  test("adds plain language and action items when the article is open", () => {
    const chunks: string[] = buildListenChunks({
      title: "Заголовок",
      subtitle: "Суть",
      plainLanguage: "Простым языком",
      actionItems: "Что сделать",
    });
    expect(chunks.join(" ")).toBe("Заголовок Суть Простым языком Что сделать");
  });
});
