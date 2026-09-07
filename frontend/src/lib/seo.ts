export const SITE_NAME: string = "newsForGermanyRU";
export const SITE_DESCRIPTION: string =
  "Новости Германии для русскоязычных читателей: политика, экономика и повседневная жизнь.";
export const DEFAULT_PUBLIC_ORIGIN: string = "https://simplenewsapp.de";
export const DEFAULT_OG_IMAGE_PATH: string = "/topic-covers/life/001.jpg";

export type RobotsDirective = "index, follow" | "noindex, nofollow";

export interface DocumentHeadSpec {
  readonly title: string;
  readonly description: string;
  readonly canonicalPath: string;
  readonly robots: RobotsDirective;
}

export interface SitemapUrl {
  readonly path: string;
  readonly changefreq: "hourly" | "monthly";
  readonly priority: string;
}

const PRIVATE_PATH_PREFIXES: readonly string[] = ["/login", "/account", "/moderation"];

/** Strips a trailing slash except for the origin itself. */
export function publicOriginFromEnv(raw: string | undefined): string {
  const trimmed: string = raw?.trim() ?? "";
  if (trimmed.length === 0) {
    return DEFAULT_PUBLIC_ORIGIN;
  }
  return trimmed.replace(/\/$/, "");
}

export function absoluteUrl(origin: string, path: string): string {
  if (path === "/" || path === "") {
    return `${origin}/`;
  }
  const normalizedPath: string = path.startsWith("/") ? path : `/${path}`;
  return `${origin}${normalizedPath}`;
}

export function isPrivateSeoPath(pathname: string): boolean {
  return PRIVATE_PATH_PREFIXES.some(
    (prefix: string): boolean => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

export function resolveDocumentHead(pathname: string): DocumentHeadSpec {
  if (isPrivateSeoPath(pathname)) {
    return {
      title: SITE_NAME,
      description: SITE_DESCRIPTION,
      canonicalPath: pathname,
      robots: "noindex, nofollow",
    };
  }
  if (pathname === "/impressum") {
    return {
      title: `Impressum — ${SITE_NAME}`,
      description: `Impressum und Anbieterkennzeichnung von ${SITE_NAME}.`,
      canonicalPath: "/impressum",
      robots: "index, follow",
    };
  }
  if (pathname === "/privacy") {
    return {
      title: `Datenschutz — ${SITE_NAME}`,
      description: `Datenschutzerklärung von ${SITE_NAME}.`,
      canonicalPath: "/privacy",
      robots: "index, follow",
    };
  }
  if (pathname === "/contact") {
    return {
      title: `Kontakt — ${SITE_NAME}`,
      description: `Kontakt und Feedback für ${SITE_NAME}.`,
      canonicalPath: "/contact",
      robots: "index, follow",
    };
  }
  if (pathname.startsWith("/news/")) {
    return {
      title: SITE_NAME,
      description: SITE_DESCRIPTION,
      canonicalPath: pathname,
      robots: "index, follow",
    };
  }
  return {
    title: `${SITE_NAME} — новости Германии`,
    description: SITE_DESCRIPTION,
    canonicalPath: "/",
    robots: "index, follow",
  };
}

export function resolveMaintenanceDocumentHead(): DocumentHeadSpec {
  return {
    title: `Überarbeitung — ${SITE_NAME}`,
    description: SITE_DESCRIPTION,
    canonicalPath: "/",
    robots: "noindex, nofollow",
  };
}

/** Homepage stays out of the sitemap while noindex is on, so Search Console does not warn. */
export function sitemapUrls(includeHome: boolean): readonly SitemapUrl[] {
  const urls: SitemapUrl[] = [];
  if (includeHome) {
    urls.push({ path: "/", changefreq: "hourly", priority: "1.0" });
  }
  urls.push(
    { path: "/impressum", changefreq: "monthly", priority: "0.4" },
    { path: "/privacy", changefreq: "monthly", priority: "0.4" },
    { path: "/contact", changefreq: "monthly", priority: "0.3" },
  );
  return urls;
}

export function buildRobotsTxt(origin: string): string {
  return [
    "User-agent: *",
    "Allow: /",
    "Disallow: /login",
    "Disallow: /account",
    "Disallow: /moderation",
    "",
    `Sitemap: ${origin}/sitemap.xml`,
    "",
  ].join("\n");
}

function escapeXml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

export function buildSitemapXml(origin: string, includeHome: boolean, lastmod: string): string {
  const entries: string[] = sitemapUrls(includeHome).map((item: SitemapUrl): string => {
    const loc: string = escapeXml(absoluteUrl(origin, item.path));
    return [
      "  <url>",
      `    <loc>${loc}</loc>`,
      `    <lastmod>${escapeXml(lastmod)}</lastmod>`,
      `    <changefreq>${item.changefreq}</changefreq>`,
      `    <priority>${item.priority}</priority>`,
      "  </url>",
    ].join("\n");
  });
  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ...entries,
    "</urlset>",
    "",
  ].join("\n");
}

