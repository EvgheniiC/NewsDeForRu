import type { Plugin, PreviewServer, ViteDevServer } from "vite";

import { parseOptionalBooleanEnv } from "./src/lib/envFlags";
import {
  DEFAULT_OG_IMAGE_PATH,
  SITE_DESCRIPTION,
  SITE_NAME,
  absoluteUrl,
  buildRobotsTxt,
  buildSitemapXml,
  publicOriginFromEnv,
} from "./src/lib/seo";

export interface SeoPluginOptions {
  readonly origin: string;
  readonly includeHomeInSitemap: boolean;
  readonly googleSiteVerification: string;
  readonly lastmod: string;
}

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function seoHeadSnippet(options: SeoPluginOptions): string {
  const origin: string = options.origin;
  const canonical: string = absoluteUrl(origin, "/");
  const image: string = absoluteUrl(origin, DEFAULT_OG_IMAGE_PATH);
  const verification: string = options.googleSiteVerification.trim();
  const verificationTag: string =
    verification.length > 0
      ? `    <meta name="google-site-verification" content="${escapeHtml(verification)}" />\n`
      : "";
  const jsonLd: string = JSON.stringify({
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: SITE_NAME,
    url: canonical,
    description: SITE_DESCRIPTION,
  });

  return [
    `    <meta name="description" content="${escapeHtml(SITE_DESCRIPTION)}" />`,
    `    <meta name="robots" content="index, follow" />`,
    `    <link rel="canonical" href="${escapeHtml(canonical)}" />`,
    `    <meta property="og:type" content="website" />`,
    `    <meta property="og:site_name" content="${escapeHtml(SITE_NAME)}" />`,
    `    <meta property="og:title" content="${escapeHtml(SITE_NAME)}" />`,
    `    <meta property="og:description" content="${escapeHtml(SITE_DESCRIPTION)}" />`,
    `    <meta property="og:url" content="${escapeHtml(canonical)}" />`,
    `    <meta property="og:image" content="${escapeHtml(image)}" />`,
    `    <meta property="og:locale" content="ru_RU" />`,
    verificationTag.trimEnd(),
    `    <script type="application/ld+json">${jsonLd}</script>`,
  ]
    .filter((line: string): boolean => line.length > 0)
    .join("\n");
}

function attachSeoMiddleware(server: ViteDevServer | PreviewServer, options: SeoPluginOptions): void {
  const robots: string = buildRobotsTxt(options.origin);
  const sitemap: string = buildSitemapXml(options.origin, options.includeHomeInSitemap, options.lastmod);
  server.middlewares.use((req, res, next): void => {
    const url: string = req.url ?? "";
    if (url === "/robots.txt") {
      res.statusCode = 200;
      res.setHeader("Content-Type", "text/plain; charset=utf-8");
      res.end(robots);
      return;
    }
    if (url === "/sitemap.xml") {
      res.statusCode = 200;
      res.setHeader("Content-Type", "application/xml; charset=utf-8");
      res.end(sitemap);
      return;
    }
    next();
  });
}

/** Emits robots.txt and sitemap.xml, and injects crawlable meta tags into index.html. */
export function seoStaticFilesPlugin(options: SeoPluginOptions): Plugin {
  const robots: string = buildRobotsTxt(options.origin);
  const sitemap: string = buildSitemapXml(options.origin, options.includeHomeInSitemap, options.lastmod);

  return {
    name: "seo-static-files",
    transformIndexHtml: {
      order: "pre",
      handler(html: string): string {
        return html.replace("<!--app-seo-->", seoHeadSnippet(options));
      },
    },
    configureServer(server: ViteDevServer): void {
      attachSeoMiddleware(server, options);
    },
    configurePreviewServer(server: PreviewServer): void {
      attachSeoMiddleware(server, options);
    },
    generateBundle(): void {
      this.emitFile({ type: "asset", fileName: "robots.txt", source: robots });
      this.emitFile({ type: "asset", fileName: "sitemap.xml", source: sitemap });
    },
  };
}

/** Production web builds stay in maintenance until VITE_MAINTENANCE_MODE is explicitly false. */
export function includeHomeInSitemap(envValue: string | undefined, isProd: boolean): boolean {
  const parsed: boolean | undefined = parseOptionalBooleanEnv(envValue);
  if (parsed !== undefined) {
    return !parsed;
  }
  return !isProd;
}

export function createSeoPluginFromEnv(env: Record<string, string>, isProd: boolean): Plugin {
  return seoStaticFilesPlugin({
    origin: publicOriginFromEnv(env.VITE_PUBLIC_APP_BASE_URL),
    includeHomeInSitemap: includeHomeInSitemap(env.VITE_MAINTENANCE_MODE, isProd),
    googleSiteVerification: env.VITE_GOOGLE_SITE_VERIFICATION?.trim() ?? "",
    lastmod: new Date().toISOString().slice(0, 10),
  });
}
