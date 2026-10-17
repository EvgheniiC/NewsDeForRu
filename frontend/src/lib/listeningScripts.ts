/** In-memory scripts so auto-next can speak a card that is already on screen. */

import type { ListenChunk } from "./listenScript";

const scripts: Map<number, readonly ListenChunk[]> = new Map();

export function registerListenScript(newsId: number, chunks: readonly ListenChunk[]): void {
  if (chunks.length === 0) {
    scripts.delete(newsId);
    return;
  }
  scripts.set(newsId, chunks);
}

export function getListenScript(newsId: number): readonly ListenChunk[] | null {
  return scripts.get(newsId) ?? null;
}

export function clearListenScripts(): void {
  scripts.clear();
}
