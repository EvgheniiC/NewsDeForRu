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
  test("pauses one and a half seconds after the title before the plain-language text", () => {
    expect(
      buildListenChunks({
        title: "Заголовок",
        plainLanguage: "Простым языком",
      }),
    ).toEqual([
      { kind: "text", text: "Заголовок" },
      { kind: "pause", durationMs: TITLE_PAUSE_MS },
      { kind: "text", text: "Простым языком" },
    ]);
    expect(TITLE_PAUSE_MS).toBe(1500);
  });

  test("skips the pause when there is no plain-language text", () => {
    expect(buildListenChunks({ title: "Только заголовок", plainLanguage: "   " })).toEqual([
      { kind: "text", text: "Только заголовок" },
    ]);
  });
});
