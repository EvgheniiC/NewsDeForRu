/** Public Google Play listing for de.simplenewsapp.app. */
export const GOOGLE_PLAY_APP_URL: string =
  "https://play.google.com/store/apps/details?id=de.simplenewsapp.app";

/** One public note about how the project is changing. Newest timestamps are shown first. */
export interface ProjectNewsItem {
  readonly id: string;
  readonly publishedAt: string;
  readonly body: string;
}

/**
 * Short public description of why the project exists.
 * Replace these paragraphs when the wording should change.
 */
export const projectGoalParagraphs: readonly string[] = [
  "Новости Германии простым русским языком. Мы собираем материалы из открытых источников, оставляем суть и коротко объясняем, что это значит в обычной жизни: политика, экономика и повседневные дела — без длинных текстов и лишнего шума.",
  "Ленту можно читать сразу, без регистрации. Главное за день собрано отдельно, срочное легко заметить, полезное — сохранить, а полный текст источника открывается, когда хочется разобраться глубже.",
];

/**
 * Project updates. Order in this list does not matter: the page sorts by `publishedAt`.
 * `publishedAt` is an ISO timestamp with offset, for example `2026-10-11T19:15:00+02:00`.
 * Separate paragraphs in `body` with a blank line.
 * A link is written as `[текст ссылки](https://example.com)`.
 */
export const projectNews: readonly ProjectNewsItem[] = [
  {
    id: "2026-10-18-audio-listening",
    publishedAt: "2026-10-18T19:24:00+02:00",
    body: "Добавили аудиопрослушивание новостей. Слушать можно только после регистрации.",
  },
  {
    id: "2026-10-11-google-play",
    publishedAt: "2026-10-11T19:15:00+02:00",
    body: `Приложение активно и уже доступно для скачивания в [Google Play](${GOOGLE_PLAY_APP_URL}).`,
  },
];

/** Returns updates from the newest timestamp to the oldest. */
export function projectNewsNewestFirst(
  items: readonly ProjectNewsItem[],
): readonly ProjectNewsItem[] {
  return [...items].sort((left: ProjectNewsItem, right: ProjectNewsItem): number =>
    right.publishedAt.localeCompare(left.publishedAt),
  );
}
