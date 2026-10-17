/** Device speech playback. One speaker at a time; pause restarts the current chunk. */

import type { ListenChunk } from "./listenScript";

export interface SpeechRequestHandlers {
  onend: () => void;
  onerror: (message: string) => void;
}

export interface SpeechEngine {
  available: boolean;
  russianVoiceReady: () => Promise<boolean>;
  speak: (text: string, handlers: SpeechRequestHandlers) => void;
  cancel: () => void;
}

export interface SpeakHandlers {
  onChunk: (index: number) => void;
  onEnd: () => void;
  onError: (message: string) => void;
}

export interface CardSpeaker {
  speak: (chunks: readonly ListenChunk[], startIndex: number, handlers: SpeakHandlers) => void;
  pause: () => void;
  resume: () => void;
  stop: () => void;
}

export const SPEECH_UNAVAILABLE_MESSAGE: string = "Озвучка на этом устройстве недоступна.";

export const RUSSIAN_VOICE_MISSING_MESSAGE: string =
  "На устройстве нет русского голоса. Установите языковой пакет синтеза речи и попробуйте снова.";

export function createCardSpeaker(engine: SpeechEngine): CardSpeaker {
  let generation: number = 0;
  let paused: boolean = false;
  let chunks: readonly ListenChunk[] = [];
  let index: number = 0;
  let handlers: SpeakHandlers | null = null;
  let silenceTimer: number | null = null;

  const clearSilence = (): void => {
    if (silenceTimer !== null) {
      window.clearTimeout(silenceTimer);
      silenceTimer = null;
    }
  };

  const beginChunk = (gen: number): void => {
    if (gen !== generation || paused || handlers === null) {
      return;
    }
    const chunk: ListenChunk | undefined = chunks[index];
    if (chunk === undefined) {
      const done: SpeakHandlers = handlers;
      handlers = null;
      done.onEnd();
      return;
    }
    handlers.onChunk(index);
    if (chunk.kind === "pause") {
      silenceTimer = window.setTimeout((): void => {
        silenceTimer = null;
        if (gen !== generation || paused) {
          return;
        }
        index += 1;
        beginChunk(gen);
      }, chunk.durationMs);
      return;
    }
    const text: string = chunk.text;
    engine.speak(text, {
      onend: (): void => {
        if (gen !== generation || paused) {
          return;
        }
        index += 1;
        beginChunk(gen);
      },
      onerror: (message: string): void => {
        if (gen !== generation || handlers === null) {
          return;
        }
        handlers.onError(message);
      },
    });
  };

  const startFromIndex = (gen: number): void => {
    if (!engine.available) {
      handlers?.onError(SPEECH_UNAVAILABLE_MESSAGE);
      return;
    }
    void engine.russianVoiceReady().then((ready: boolean): void => {
      if (gen !== generation || paused || handlers === null) {
        return;
      }
      if (!ready) {
        handlers.onError(RUSSIAN_VOICE_MISSING_MESSAGE);
        return;
      }
      beginChunk(gen);
    });
  };

  return {
    speak(nextChunks: readonly ListenChunk[], startIndex: number, nextHandlers: SpeakHandlers): void {
      generation += 1;
      const gen: number = generation;
      paused = false;
      clearSilence();
      engine.cancel();
      chunks = nextChunks;
      index = startIndex < 0 ? 0 : startIndex;
      handlers = nextHandlers;
      if (chunks.length === 0 || index >= chunks.length) {
        handlers = null;
        nextHandlers.onEnd();
        return;
      }
      startFromIndex(gen);
    },
    pause(): void {
      if (handlers === null || paused) {
        return;
      }
      paused = true;
      generation += 1;
      clearSilence();
      engine.cancel();
    },
    resume(): void {
      if (!paused || handlers === null) {
        return;
      }
      paused = false;
      generation += 1;
      startFromIndex(generation);
    },
    stop(): void {
      generation += 1;
      paused = false;
      handlers = null;
      chunks = [];
      index = 0;
      clearSilence();
      engine.cancel();
    },
  };
}

const VOICE_WAIT_MS: number = 1500;

function voiceLang(voice: SpeechSynthesisVoice): string {
  return voice.lang.toLowerCase();
}

export function pickRussianVoice(voices: readonly SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  const russian: SpeechSynthesisVoice[] = voices.filter((voice: SpeechSynthesisVoice) =>
    voiceLang(voice).startsWith("ru"),
  );
  if (russian.length === 0) {
    return null;
  }
  const exact: SpeechSynthesisVoice | undefined = russian.find(
    (voice: SpeechSynthesisVoice) => voiceLang(voice) === "ru-ru",
  );
  return exact ?? russian[0];
}

function waitForRussianVoice(synth: SpeechSynthesis): Promise<boolean> {
  if (pickRussianVoice(synth.getVoices()) !== null) {
    return Promise.resolve(true);
  }
  return new Promise<boolean>((resolve: (ready: boolean) => void): void => {
    const finish = (ready: boolean): void => {
      window.clearTimeout(timer);
      synth.removeEventListener("voiceschanged", onVoices);
      resolve(ready);
    };
    const onVoices = (): void => {
      if (pickRussianVoice(synth.getVoices()) !== null) {
        finish(true);
      }
    };
    const timer: number = window.setTimeout((): void => {
      finish(pickRussianVoice(synth.getVoices()) !== null);
    }, VOICE_WAIT_MS);
    synth.addEventListener("voiceschanged", onVoices);
    synth.getVoices();
  });
}

/** Web Speech API adapter. Cancelled utterances are ignored so pause does not look like a failure. */
export function createBrowserSpeechEngine(): SpeechEngine {
  const synth: SpeechSynthesis | undefined =
    typeof window !== "undefined" ? window.speechSynthesis : undefined;
  let token: number = 0;

  return {
    available: synth !== undefined,
    russianVoiceReady: (): Promise<boolean> => {
      if (synth === undefined) {
        return Promise.resolve(false);
      }
      return waitForRussianVoice(synth);
    },
    speak: (text: string, handlers: SpeechRequestHandlers): void => {
      if (synth === undefined) {
        handlers.onerror(SPEECH_UNAVAILABLE_MESSAGE);
        return;
      }
      token += 1;
      const myToken: number = token;
      synth.cancel();
      window.setTimeout((): void => {
        if (myToken !== token || synth === undefined) {
          return;
        }
        const utterance: SpeechSynthesisUtterance = new SpeechSynthesisUtterance(text);
        utterance.lang = "ru-RU";
        utterance.rate = 1;
        const voice: SpeechSynthesisVoice | null = pickRussianVoice(synth.getVoices());
        if (voice !== null) {
          utterance.voice = voice;
        }
        utterance.onend = (): void => {
          if (myToken !== token) {
            return;
          }
          handlers.onend();
        };
        utterance.onerror = (event: SpeechSynthesisErrorEvent): void => {
          if (myToken !== token) {
            return;
          }
          if (event.error === "interrupted" || event.error === "canceled") {
            return;
          }
          handlers.onerror("Не удалось озвучить фрагмент.");
        };
        synth.speak(utterance);
      }, 0);
    },
    cancel: (): void => {
      token += 1;
      synth?.cancel();
    },
  };
}
