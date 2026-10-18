interface OpenSourceFiguresProps {
  figures: string;
}

interface OpenSourceMeaningProps {
  meaning: string;
}

export function figureLines(raw: string): string[] {
  return raw
    .split(/\n+/)
    .map((line: string): string => line.trim())
    .filter((line: string): boolean => line.length > 0)
    .map((line: string): string => (line.startsWith("- ") ? line.slice(2).trim() : line))
    .filter((line: string): boolean => line.length > 0);
}

/** Short figures list on an open-source card. */
export function OpenSourceFigures({ figures }: OpenSourceFiguresProps): JSX.Element | null {
  const lines: string[] = figureLines(figures);
  if (lines.length === 0) {
    return null;
  }
  return (
    <div className="news-card-figures">
      <p className="news-card-figures__label">Цифры</p>
      <ul className="news-card-figures__list">
        {lines.map((line: string, index: number) => (
          <li key={`${index}-${line}`}>{line}</li>
        ))}
      </ul>
    </div>
  );
}

/** One short "what this means" paragraph on an open-source card. */
export function OpenSourceMeaning({ meaning }: OpenSourceMeaningProps): JSX.Element | null {
  const text: string = meaning.trim();
  if (text.length === 0) {
    return null;
  }
  return (
    <p className="news-card-meaning">
      <strong>Что это значит: </strong>
      {text}
    </p>
  );
}
