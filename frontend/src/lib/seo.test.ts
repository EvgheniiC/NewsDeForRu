import { afterEach, expect, test } from "vitest";

import { applyDocumentHead } from "./documentHead";
import {
  buildRobotsTxt,
  buildSitemapXml,
  publicOriginFromEnv,
  resolveDocumentHead,
  resolveMaintenanceDocumentHead,
  sitemapUrls,
} from "./seo";

afterEach((): void => {
  document.title = "";
  document.head.querySelectorAll("meta[name='description'], meta[name='robots'], meta[property], link[rel='canonical']").forEach(
    (node: Element): void => {
      node.remove();
    },
  );
});

test("publicOriginFromEnv strips a trailing slash", (): void => {
  expect(publicOriginFromEnv("https://simplenewsapp.de/")).toBe("https://simplenewsapp.de");
  expect(publicOriginFromEnv(undefined)).toBe("https://simplenewsapp.de");
});

test("resolveDocumentHead indexes legal pages and blocks private routes", (): void => {
  expect(resolveDocumentHead("/impressum").robots).toBe("index, follow");
  expect(resolveDocumentHead("/privacy").title).toContain("Datenschutz");
  expect(resolveDocumentHead("/contact").canonicalPath).toBe("/contact");
  expect(resolveDocumentHead("/login").robots).toBe("noindex, nofollow");
  expect(resolveDocumentHead("/account/reset").robots).toBe("noindex, nofollow");
  expect(resolveDocumentHead("/moderation").robots).toBe("noindex, nofollow");
  expect(resolveDocumentHead("/").robots).toBe("index, follow");
});

test("resolveMaintenanceDocumentHead keeps the reconstruction page out of the index", (): void => {
  expect(resolveMaintenanceDocumentHead().robots).toBe("noindex, nofollow");
  expect(resolveMaintenanceDocumentHead().canonicalPath).toBe("/");
});

test("sitemap omits the homepage while it is noindex", (): void => {
  expect(sitemapUrls(false).map((item) => item.path)).toEqual(["/impressum", "/privacy", "/contact"]);
  expect(sitemapUrls(true)[0]?.path).toBe("/");
});

test("buildRobotsTxt points crawlers at the sitemap and hides account routes", (): void => {
  const robots: string = buildRobotsTxt("https://simplenewsapp.de");
  expect(robots).toContain("Allow: /");
  expect(robots).toContain("Disallow: /account");
  expect(robots).toContain("Sitemap: https://simplenewsapp.de/sitemap.xml");
});

test("buildSitemapXml includes lastmod and homepage only when asked", (): void => {
  const withoutHome: string = buildSitemapXml("https://simplenewsapp.de", false, "2026-09-07");
  expect(withoutHome).not.toContain("<loc>https://simplenewsapp.de/</loc>");
  expect(withoutHome).toContain("<loc>https://simplenewsapp.de/impressum</loc>");

  const withHome: string = buildSitemapXml("https://simplenewsapp.de", true, "2026-09-07");
  expect(withHome).toContain("<loc>https://simplenewsapp.de/</loc>");
  expect(withHome).toContain("<lastmod>2026-09-07</lastmod>");
});

test("applyDocumentHead writes robots and restores the previous title", (): void => {
  document.title = "before";
  const restore: () => void = applyDocumentHead(
    {
      title: "Impressum — newsForGermanyRU",
      description: "Impressum",
      canonicalPath: "/impressum",
      robots: "index, follow",
    },
    "https://simplenewsapp.de",
  );

  expect(document.title).toBe("Impressum — newsForGermanyRU");
  expect(document.head.querySelector('meta[name="robots"]')?.getAttribute("content")).toBe("index, follow");
  expect(document.head.querySelector('link[rel="canonical"]')?.getAttribute("href")).toBe(
    "https://simplenewsapp.de/impressum",
  );

  restore();
  expect(document.title).toBe("before");
});
