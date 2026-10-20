import type { FeedFilterKey } from "../types/news";

export interface FeedEmptyStateCopy {
  readonly lead: string;
  readonly detail: string;
}

export type ActiveFeedFilter = Exclude<FeedFilterKey, "saved_useful" | "read_saved">;

/**
 * Short empty-state copy for the live feed.
 * Economy and politics stay as tabs; the text explains why they can be empty.
 */
export function feedEmptyStateCopy(filter: ActiveFeedFilter): FeedEmptyStateCopy {
  switch (filter) {
    case "economy":
      return {
        lead: "В «Экономике» пока пусто.",
        detail:
          "Цифры берём из открытой статистики — Destatis и Eurostat. Они выходят не каждый день, поэтому вкладка иногда без карточек. Лента обновится сама."
      };
    case "politics":
      return {
        lead: "В «Политике» пока пусто.",
        detail:
          "Здесь только официальные сообщения, без пересказа газет. Релизы выходят не каждый день, поэтому вкладка иногда без карточек. Лента обновится сама."
      };
    case "urgent":
      return {
        lead: "Сейчас нет ничего, что нужно сделать сегодня.",
        detail: "Срочные карточки появляются по официальным сообщениям. Лента обновляется автоматически."
      };
    case "for_me":
      return {
        lead: "По выбранным темам пока пусто.",
        detail: "Карточки с этими темами появятся с ближайшим релизом. Остальные новости тоже остаются в этой ленте."
      };
    case "life":
    case "positive":
    case "top_today":
      return {
        lead: "Пока нет новостей в этой подборке.",
        detail:
          "Сейчас материалов мало: публикуем только открытые источники. Новая карточка появится с ближайшим релизом."
      };
    default: {
      const _exhaustive: never = filter;
      return _exhaustive;
    }
  }
}
