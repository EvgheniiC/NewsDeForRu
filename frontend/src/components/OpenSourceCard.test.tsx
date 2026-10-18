import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, test } from "vitest";

import { NewsArticleBody } from "./NewsArticleBody";
import { figureLines, OpenSourceFigures, OpenSourceMeaning } from "./OpenSourceFigures";
import type { ProcessedNews } from "../types/news";

afterEach((): void => {
  cleanup();
});

function processed(overrides: Partial<ProcessedNews> = {}): ProcessedNews {
  return {
    id: 7,
    title: "Инфляция в Германии",
    one_sentence_summary: "Рост цен замедлился. В сентябре показатель составил 2,4 процента.",
    plain_language: "Проще говоря, покупать продукты стало чуть дороже, чем год назад.",
    impact_presentation: "single",
    impact_unified: "Для жителей это означает более дорогую продуктовую корзину.",
    impact_owner: "",
    impact_tenant: "",
    impact_buyer: "",
    action_items: "",
    bonus_block: "- 2,4 %\n- 1,8 %",
    spoiler: "",
    source_url: "https://ec.europa.eu/eurostat/example",
    confidence_score: 0.8,
    publication_status: "published",
    read_time_minutes: 2,
    topic: "economy",
    is_urgent: false,
    is_positive: false,
    published_at: "2026-10-01T08:00:00+02:00",
    source_name: "Eurostat",
    created_at: "2026-10-01T08:00:00+02:00",
    ...overrides
  };
}

describe("open source card", () => {
  test("figure lines drop the bullet marker", () => {
    expect(figureLines("- 2,4 %\n- 83,6 млн")).toEqual(["2,4 %", "83,6 млн"]);
  });

  test("collapsed card blocks stay empty without figures or meaning", () => {
    const { rerender } = render(
      <>
        <OpenSourceFigures figures="- 2,4 %" />
        <OpenSourceMeaning meaning="Для жителей это означает более дорогую корзину." />
      </>
    );

    expect(screen.getByText("Цифры")).toBeTruthy();
    expect(screen.getByText("2,4 %")).toBeTruthy();
    expect(screen.getByText(/Для жителей это означает/)).toBeTruthy();

    rerender(
      <>
        <OpenSourceFigures figures="" />
        <OpenSourceMeaning meaning="" />
      </>
    );
    expect(screen.queryByText("Цифры")).toBeNull();
    expect(screen.queryByText(/Что это значит/)).toBeNull();
  });

  test("article keeps the longer lead and does not repeat figures as extra text", () => {
    render(
      <NewsArticleBody
        includeMobileExtras={false}
        news={processed({ extended_card: true, key_figures: "- 2,4 %\n- 1,8 %" })}
      />
    );

    expect(screen.getByText(/Рост цен замедлился/)).toBeTruthy();
    expect(screen.getByText("Цифры")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Что это значит" })).toBeTruthy();
    expect(screen.queryByText(/Дополнительно/)).toBeNull();
  });

  test("publisher article stays a short plain-language card", () => {
    render(
      <NewsArticleBody
        includeMobileExtras={false}
        news={processed({
          extended_card: false,
          key_figures: "",
          bonus_block: "",
          impact_presentation: "none",
          impact_unified: "",
          one_sentence_summary: "Одно предложение."
        })}
      />
    );

    expect(screen.queryByText("Цифры")).toBeNull();
    expect(screen.queryByText("Одно предложение.")).toBeNull();
    expect(screen.getByText(/Проще говоря/)).toBeTruthy();
  });
});
