/** Android/iOS speech via the system TTS engine. WebView speechSynthesis is often missing. */

import { QueueStrategy, TextToSpeech } from "@capacitor-community/text-to-speech";
import {
  RUSSIAN_VOICE_MISSING_MESSAGE,
  SPEECH_UNAVAILABLE_MESSAGE,
  type SpeechEngine,
  type SpeechRequestHandlers,
} from "./cardTts";

const INIT_RETRY_MS: number = 300;
const INIT_ATTEMPTS: number = 6;

function delay(ms: number): Promise<void> {
  return new Promise((resolve: () => void): void => {
    window.setTimeout(resolve, ms);
  });
}

function errorMessage(error: unknown): string {
  if (typeof error === "object" && error !== null && "message" in error) {
    const message: unknown = (error as { message: unknown }).message;
    if (typeof message === "string") {
      return message;
    }
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "";
}

function isNotInitialized(message: string): boolean {
  return message.toLowerCase().includes("not yet initialized");
}

function isMissingLanguage(message: string): boolean {
  return message.toLowerCase().includes("not supported");
}

async function supportedRussianLang(): Promise<string | null> {
  const tags: readonly string[] = ["ru-RU", "ru"];
  for (let attempt: number = 0; attempt < INIT_ATTEMPTS; attempt += 1) {
    try {
      for (const tag of tags) {
        const result: { supported: boolean } = await TextToSpeech.isLanguageSupported({ lang: tag });
        if (result.supported) {
          return tag;
        }
      }
    } catch (error: unknown) {
      const message: string = errorMessage(error);
      if (!isNotInitialized(message) && !message.toLowerCase().includes("not available")) {
        return null;
      }
    }
    if (attempt < INIT_ATTEMPTS - 1) {
      await delay(INIT_RETRY_MS);
    }
  }
  return null;
}

async function speakWithRetry(text: string, lang: string): Promise<void> {
  let lastError: unknown = null;
  for (let attempt: number = 0; attempt < INIT_ATTEMPTS; attempt += 1) {
    try {
      await TextToSpeech.speak({
        text,
        lang,
        rate: 1,
        pitch: 1,
        volume: 1,
        queueStrategy: QueueStrategy.Flush,
      });
      return;
    } catch (error: unknown) {
      lastError = error;
      if (isNotInitialized(errorMessage(error)) && attempt < INIT_ATTEMPTS - 1) {
        await delay(INIT_RETRY_MS);
        continue;
      }
      throw error;
    }
  }
  throw lastError;
}

/** Native engine. `available` stays true; a missing Russian voice is reported separately. */
export function createNativeSpeechEngine(): SpeechEngine {
  let token: number = 0;
  let lang: string = "ru-RU";

  return {
    available: true,
    russianVoiceReady: async (): Promise<boolean> => {
      const supported: string | null = await supportedRussianLang();
      if (supported === null) {
        return false;
      }
      lang = supported;
      return true;
    },
    speak: (text: string, handlers: SpeechRequestHandlers): void => {
      token += 1;
      const myToken: number = token;
      void speakWithRetry(text, lang)
        .then((): void => {
          if (myToken !== token) {
            return;
          }
          handlers.onend();
        })
        .catch((error: unknown): void => {
          if (myToken !== token) {
            return;
          }
          const message: string = errorMessage(error);
          if (isMissingLanguage(message)) {
            handlers.onerror(RUSSIAN_VOICE_MISSING_MESSAGE);
            return;
          }
          if (isNotInitialized(message) || message.toLowerCase().includes("not available")) {
            handlers.onerror(SPEECH_UNAVAILABLE_MESSAGE);
            return;
          }
          handlers.onerror("Не удалось озвучить фрагмент.");
        });
    },
    cancel: (): void => {
      token += 1;
      void TextToSpeech.stop();
    },
  };
}
