import { describe, expect, it } from "vitest";

import { newsTopicCoverSrc } from "./topicCovers";

describe("newsTopicCoverSrc", () => {
  it("picks a stable file from the topic pool", () => {
    expect(newsTopicCoverSrc("economy", 10)).toBe("/topic-covers/economy/001.jpg");
    expect(newsTopicCoverSrc("economy", 10)).toBe("/topic-covers/economy/001.jpg");
  });

  it("prefers the cover tag folder over the feed topic", () => {
    const src: string = newsTopicCoverSrc("life", 10, "sport");
    expect(src.startsWith("/topic-covers/sport/")).toBe(true);
  });

  it("falls back to the topic folder when the tag is missing", () => {
    expect(newsTopicCoverSrc("life", 10)).toBe("/topic-covers/life/001.jpg");
  });
});
