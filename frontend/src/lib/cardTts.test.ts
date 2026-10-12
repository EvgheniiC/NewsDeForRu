import { describe, expect, test } from "vitest";
import {
  RUSSIAN_VOICE_MISSING_MESSAGE,
  SPEECH_UNAVAILABLE_MESSAGE,
  createCardSpeaker,
  pickRussianVoice,
  type CardSpeaker,
  type SpeechEngine,
  type SpeechRequestHandlers,
} from "./cardTts";

interface FakeEngine extends SpeechEngine {
  spoken: string[];
  finish: () => void;
}

function createFakeEngine(ready: boolean, available: boolean = true): FakeEngine {
  let current: SpeechRequestHandlers | null = null;
  const spoken: string[] = [];
  return {
    available,
    spoken,
    russianVoiceReady: (): Promise<boolean> => Promise.resolve(ready),
    speak: (text: string, handlers: SpeechRequestHandlers): void => {
      spoken.push(text);
      current = handlers;
    },
    cancel: (): void => {
      current = null;
    },
    finish: (): void => {
      const handlers: SpeechRequestHandlers | null = current;
      current = null;
      handlers?.onend();
    },
  };
}

async function flushMicrotasks(): Promise<void> {
  await Promise.resolve();
  await Promise.resolve();
}

describe("createCardSpeaker", () => {
  test("speaks chunks in order and reports the end", async () => {
    const engine: FakeEngine = createFakeEngine(true);
    const speaker: CardSpeaker = createCardSpeaker(engine);
    const seen: number[] = [];
    let ended: boolean = false;
    speaker.speak(["раз", "два"], 0, {
      onChunk: (index: number): void => {
        seen.push(index);
      },
      onEnd: (): void => {
        ended = true;
      },
      onError: (): void => {
        throw new Error("unexpected error");
      },
    });
    await flushMicrotasks();
    expect(seen).toEqual([0]);
    expect(engine.spoken).toEqual(["раз"]);
    engine.finish();
    expect(seen).toEqual([0, 1]);
    engine.finish();
    expect(ended).toBe(true);
  });

  test("resumes the same chunk after pause", async () => {
    const engine: FakeEngine = createFakeEngine(true);
    const speaker: CardSpeaker = createCardSpeaker(engine);
    speaker.speak(["раз", "два"], 0, {
      onChunk: (): void => undefined,
      onEnd: (): void => undefined,
      onError: (): void => undefined,
    });
    await flushMicrotasks();
    speaker.pause();
    engine.finish();
    speaker.resume();
    await flushMicrotasks();
    expect(engine.spoken).toEqual(["раз", "раз"]);
  });

  test("reports a missing Russian voice without speaking", async () => {
    const engine: FakeEngine = createFakeEngine(false);
    const speaker: CardSpeaker = createCardSpeaker(engine);
    let message: string = "";
    speaker.speak(["раз"], 0, {
      onChunk: (): void => undefined,
      onEnd: (): void => undefined,
      onError: (errorMessage: string): void => {
        message = errorMessage;
      },
    });
    await flushMicrotasks();
    expect(message).toBe(RUSSIAN_VOICE_MISSING_MESSAGE);
    expect(engine.spoken).toEqual([]);
  });

  test("reports when speech synthesis is missing", () => {
    const engine: FakeEngine = createFakeEngine(true, false);
    const speaker: CardSpeaker = createCardSpeaker(engine);
    let message: string = "";
    speaker.speak(["раз"], 0, {
      onChunk: (): void => undefined,
      onEnd: (): void => undefined,
      onError: (errorMessage: string): void => {
        message = errorMessage;
      },
    });
    expect(message).toBe(SPEECH_UNAVAILABLE_MESSAGE);
  });
});

describe("pickRussianVoice", () => {
  test("prefers ru-RU", () => {
    const voices: SpeechSynthesisVoice[] = [
      { lang: "en-US", name: "English" } as SpeechSynthesisVoice,
      { lang: "ru-RU", name: "Russian" } as SpeechSynthesisVoice,
      { lang: "ru", name: "Generic" } as SpeechSynthesisVoice,
    ];
    expect(pickRussianVoice(voices)?.name).toBe("Russian");
  });
});
