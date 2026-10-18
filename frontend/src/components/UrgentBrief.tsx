import { figureLines } from "./OpenSourceFigures";

interface UrgentBriefProps {
  happened: string;
  affects: string;
  actionToday: string;
}

interface BriefBlockProps {
  label: string;
  text: string;
}

function isBulleted(text: string): boolean {
  return text
    .split(/\n+/)
    .map((line: string): string => line.trim())
    .filter((line: string): boolean => line.length > 0)
    .some((line: string): boolean => line.startsWith("- "));
}

function BriefBlock({ label, text }: BriefBlockProps): JSX.Element | null {
  const trimmed: string = text.trim();
  if (trimmed.length === 0) {
    return null;
  }
  if (!isBulleted(trimmed)) {
    return (
      <p className="news-card-urgent-brief__line">
        <strong>{label}: </strong>
        {trimmed}
      </p>
    );
  }
  const lines: string[] = figureLines(trimmed);
  return (
    <div>
      <p className="news-card-urgent-brief__label">{label}</p>
      <ul className="news-card-urgent-brief__list">
        {lines.map((line: string, index: number) => (
          <li key={`${index}-${line}`}>{line}</li>
        ))}
      </ul>
    </div>
  );
}

/** Collapsed urgent-tab card: what happened, who it affects, what to do today. */
export function UrgentBrief({ happened, affects, actionToday }: UrgentBriefProps): JSX.Element | null {
  const happenedText: string = happened.trim();
  const affectsText: string = affects.trim();
  const actionText: string = actionToday.trim();
  if (happenedText.length === 0 && affectsText.length === 0 && actionText.length === 0) {
    return null;
  }
  return (
    <div className="news-card-urgent-brief">
      <BriefBlock label="Что случилось" text={happenedText} />
      <BriefBlock label="Кого касается" text={affectsText} />
      <BriefBlock label="Что сделать сегодня" text={actionText} />
    </div>
  );
}
