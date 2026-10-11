import { type ReactNode } from "react";
import {
  projectGoalParagraphs,
  projectNews,
  projectNewsNewestFirst,
  type ProjectNewsItem,
} from "../content/about/projectAbout";
import { APP_TIME_ZONE } from "../lib/dateTimeBerlin";

const NEWS_LINK_PATTERN: RegExp = /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;

function newsParagraphs(body: string): readonly string[] {
  return body
    .split(/\n\n+/)
    .map((paragraph: string): string => paragraph.trim())
    .filter((paragraph: string): boolean => paragraph.length > 0);
}

function formatProjectNewsDateTime(publishedAt: string): string {
  const parsed: Date = new Date(publishedAt);
  if (Number.isNaN(parsed.getTime())) {
    return publishedAt;
  }
  return new Intl.DateTimeFormat("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: APP_TIME_ZONE,
  }).format(parsed);
}

function renderNewsText(text: string): ReactNode[] {
  const nodes: ReactNode[] = [];
  let lastIndex: number = 0;
  NEWS_LINK_PATTERN.lastIndex = 0;
  for (const match of text.matchAll(NEWS_LINK_PATTERN)) {
    const fullMatch: string = match[0];
    const label: string = match[1] ?? "";
    const href: string = match[2] ?? "";
    const start: number = match.index ?? 0;
    if (start > lastIndex) {
      nodes.push(text.slice(lastIndex, start));
    }
    nodes.push(
      <a href={href} key={`${href}-${start}`} rel="noopener noreferrer" target="_blank">
        {label}
      </a>,
    );
    lastIndex = start + fullMatch.length;
  }
  if (lastIndex < text.length) {
    nodes.push(text.slice(lastIndex));
  }
  return nodes;
}

export function AboutPage(): JSX.Element {
  const updates: readonly ProjectNewsItem[] = projectNewsNewestFirst(projectNews);

  return (
    <section className="legal-page about-page">
      <h1>О проекте</h1>
      {projectGoalParagraphs.map((paragraph: string) => (
        <p key={paragraph}>{paragraph}</p>
      ))}

      <h2>Новости проекта</h2>
      {updates.length === 0 ? (
        <p className="muted">Здесь будут короткие заметки о том, что меняется в проекте.</p>
      ) : (
        <ol className="about-news-list">
          {updates.map((item: ProjectNewsItem) => (
            <li className="about-news-item" key={item.id}>
              <p className="about-news-date">
                <time dateTime={item.publishedAt}>{formatProjectNewsDateTime(item.publishedAt)}</time>
              </p>
              {newsParagraphs(item.body).map((paragraph: string) => (
                <p className="about-news-body" key={paragraph}>
                  {renderNewsText(paragraph)}
                </p>
              ))}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
