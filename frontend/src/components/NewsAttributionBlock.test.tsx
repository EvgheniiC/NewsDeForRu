import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { NewsAttributionBlock } from "./NewsAttributionBlock";

describe("NewsAttributionBlock", () => {
  it("shows licence and change notice for an open source", () => {
    render(
      <NewsAttributionBlock
        changesNotice="Неофициальный перевод и AI-суммаризация."
        copyrightHolder="European Union"
        licence="CC BY 4.0"
        licenceUrl="https://creativecommons.org/licenses/by/4.0/"
        originalLanguage="en"
        originalTitle="Original title"
        publishedAt="2026-08-02T10:00:00Z"
        retrievedAt="2026-08-02T11:00:00Z"
        sourceName="European Commission Press Corner"
        sourceUrl="https://ec.europa.eu/example"
      />
    );

    expect(screen.getByText(/Original title/)).toBeTruthy();
    expect(screen.getByText("CC BY 4.0").getAttribute("href")).toBe(
      "https://creativecommons.org/licenses/by/4.0/"
    );
    expect(screen.getByText(/Неофициальный перевод/)).toBeTruthy();
  });
});
