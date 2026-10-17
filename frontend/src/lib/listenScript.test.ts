import { describe, expect, test } from "vitest";
import { TITLE_PAUSE_MS, buildListenChunks, splitSpeechText } from "./listenScript";

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
  test("pauses one and a half seconds after the title before the news", () => {
    expect(
      buildListenChunks({
        title: "Заголовок",
        subtitle: "Суть новости",
      }),
    ).toEqual([
      { kind: "text", text: "Заголовок" },
      { kind: "pause", durationMs: TITLE_PAUSE_MS },
      { kind: "text", text: "Суть новости" },
    ]);
    expect(TITLE_PAUSE_MS).toBe(1500);
  });

  test("adds plain language and action items after the title pause", () => {
    expect(
      buildListenChunks({
        title: "Заголовок",
        subtitle: "Суть",
        plainLanguage: "Простым языком",
        actionItems: "Что сделать",
      }),
    ).toEqual([
      { kind: "text", text: "Заголовок" },
      { kind: "pause", durationMs: TITLE_PAUSE_MS },
      { kind: "text", text: "Суть Простым языком Что сделать" },
    ]);
  });

  test("skips the pause when there is no body", () => {
    expect(buildListenChunks({ title: "Только заголовок", subtitle: "   " })).toEqual([
      { kind: "text", text: "Только заголовок" },
    ]);
  });
});
