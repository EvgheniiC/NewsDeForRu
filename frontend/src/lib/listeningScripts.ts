/** In-memory scripts so auto-next can speak a card that is already on screen. */

import type { ListenChunk } from "./listenScript";

const scripts: Map<number, readonly ListenChunk[]> = new Map();

export function registerListenScript(newsId: number, chunks: readonly ListenChunk[]): void {
  if (chunks.length === 0) {
    return;
  }
  const current: readonly ListenChunk[] | undefined = scripts.get(newsId);
  if (current !== undefined && current.length > chunks.length) {
    return;
  }
  scripts.set(newsId, chunks);
}

/** Uses the longer copy so a title-only card cannot replace the script already being spoken. */
export function preferListenScript(newsId: number, chunks: readonly ListenChunk[]): readonly ListenChunk[] {
  const saved: readonly ListenChunk[] | undefined = scripts.get(newsId);
  if (saved !== undefined && saved.length > chunks.length) {
    return saved;
  }
  return chunks;
}

export function getListenScript(newsId: number): readonly ListenChunk[] | null {
  return scripts.get(newsId) ?? null;
}

export function clearListenScripts(): void {
  scripts.clear();
}
