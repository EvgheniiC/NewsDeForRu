/** Picks the system speech engine on Android and the browser engine on the web. */

import { Capacitor } from "@capacitor/core";
import { createBrowserSpeechEngine, createCardSpeaker, type CardSpeaker } from "./cardTts";
import { createNativeSpeechEngine } from "./nativeSpeechEngine";

let speaker: CardSpeaker | null = null;

export function getCardSpeaker(): CardSpeaker {
  if (speaker === null) {
    const native: boolean = Capacitor.isNativePlatform();
    speaker = createCardSpeaker(native ? createNativeSpeechEngine() : createBrowserSpeechEngine());
  }
  return speaker;
}
