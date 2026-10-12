/** In-memory scripts so auto-next can speak a card that is already on screen. */

const scripts: Map<number, readonly string[]> = new Map();

export function registerListenScript(newsId: number, chunks: readonly string[]): void {
  if (chunks.length === 0) {
    scripts.delete(newsId);
    return;
  }
  scripts.set(newsId, chunks);
}

export function getListenScript(newsId: number): readonly string[] | null {
  return scripts.get(newsId) ?? null;
}

export function clearListenScripts(): void {
  scripts.clear();
}
