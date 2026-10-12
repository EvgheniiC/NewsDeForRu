/** Spoken text for one news card. Licences, URLs, and badges are left out. */

export const MAX_SPEECH_CHUNK_CHARS: number = 140;

export interface ListenScriptInput {
  title: string;
  subtitle: string;
  plainLanguage?: string | null;
  actionItems?: string | null;
}

function normalizeSpeechText(raw: string): string {
  return raw.replace(/\s+/g, " ").trim();
}

function splitByWords(text: string, maxChars: number): string[] {
  const words: string[] = text.split(" ");
  const parts: string[] = [];
  let current: string = "";
  for (const word of words) {
    if (word.length === 0) {
      continue;
    }
    if (word.length > maxChars) {
      if (current.length > 0) {
        parts.push(current);
        current = "";
      }
      for (let offset: number = 0; offset < word.length; offset += maxChars) {
        parts.push(word.slice(offset, offset + maxChars));
      }
      continue;
    }
    if (current.length === 0) {
      current = word;
      continue;
    }
    if (current.length + 1 + word.length <= maxChars) {
      current = `${current} ${word}`;
      continue;
    }
    parts.push(current);
    current = word;
  }
  if (current.length > 0) {
    parts.push(current);
  }
  return parts;
}

/** Android and Chrome cut off a single utterance, so text is split into short pieces. */
export function splitSpeechText(text: string, maxChars: number = MAX_SPEECH_CHUNK_CHARS): string[] {
  const normalized: string = normalizeSpeechText(text);
  if (normalized.length === 0 || maxChars <= 0) {
    return [];
  }
  const sentences: string[] = normalized.split(/(?<=[.!?…])\s+/u);
  const chunks: string[] = [];
  let current: string = "";
  const pushPiece = (piece: string): void => {
    const parts: string[] = piece.length <= maxChars ? [piece] : splitByWords(piece, maxChars);
    for (const part of parts) {
      if (current.length === 0) {
        current = part;
        continue;
      }
      if (current.length + 1 + part.length <= maxChars) {
        current = `${current} ${part}`;
        continue;
      }
      chunks.push(current);
      current = part;
    }
  };
  for (const sentence of sentences) {
    const trimmed: string = sentence.trim();
    if (trimmed.length > 0) {
      pushPiece(trimmed);
    }
  }
  if (current.length > 0) {
    chunks.push(current);
  }
  return chunks;
}

/** Preview is title + subtitle. Expanded article adds plain language and action items. */
export function buildListenChunks(input: ListenScriptInput): string[] {
  const parts: string[] = [input.title, input.subtitle];
  if (typeof input.plainLanguage === "string" && input.plainLanguage.trim().length > 0) {
    parts.push(input.plainLanguage);
  }
  if (typeof input.actionItems === "string" && input.actionItems.trim().length > 0) {
    parts.push(input.actionItems);
  }
  return splitSpeechText(parts.filter((part: string) => normalizeSpeechText(part).length > 0).join(" "));
}
