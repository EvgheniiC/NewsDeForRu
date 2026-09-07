import { absoluteUrl, type DocumentHeadSpec } from "./seo";

function upsertNamedMeta(name: string, content: string): HTMLMetaElement {
  const selector: string = `meta[name="${name}"]`;
  const existing: HTMLMetaElement | null = document.head.querySelector(selector);
  const element: HTMLMetaElement = existing ?? document.createElement("meta");
  element.setAttribute("name", name);
  element.setAttribute("content", content);
  if (existing === null) {
    document.head.appendChild(element);
  }
  return element;
}

function upsertPropertyMeta(property: string, content: string): HTMLMetaElement {
  const selector: string = `meta[property="${property}"]`;
  const existing: HTMLMetaElement | null = document.head.querySelector(selector);
  const element: HTMLMetaElement = existing ?? document.createElement("meta");
  element.setAttribute("property", property);
  element.setAttribute("content", content);
  if (existing === null) {
    document.head.appendChild(element);
  }
  return element;
}

function upsertCanonical(href: string): HTMLLinkElement {
  const existing: HTMLLinkElement | null = document.head.querySelector('link[rel="canonical"]');
  const element: HTMLLinkElement = existing ?? document.createElement("link");
  element.setAttribute("rel", "canonical");
  element.setAttribute("href", href);
  if (existing === null) {
    document.head.appendChild(element);
  }
  return element;
}

/** Applies title, description, robots, canonical and Open Graph tags. Returns a restore callback. */
export function applyDocumentHead(spec: DocumentHeadSpec, origin: string): () => void {
  const previousTitle: string = document.title;
  const previousDescription: string =
    document.head.querySelector('meta[name="description"]')?.getAttribute("content") ?? "";
  const previousRobots: string =
    document.head.querySelector('meta[name="robots"]')?.getAttribute("content") ?? "";
  const previousCanonical: string =
    document.head.querySelector('link[rel="canonical"]')?.getAttribute("href") ?? "";
  const previousOgTitle: string =
    document.head.querySelector('meta[property="og:title"]')?.getAttribute("content") ?? "";
  const previousOgDescription: string =
    document.head.querySelector('meta[property="og:description"]')?.getAttribute("content") ?? "";
  const previousOgUrl: string =
    document.head.querySelector('meta[property="og:url"]')?.getAttribute("content") ?? "";

  const canonicalHref: string = absoluteUrl(origin, spec.canonicalPath);
  document.title = spec.title;
  upsertNamedMeta("description", spec.description);
  upsertNamedMeta("robots", spec.robots);
  upsertCanonical(canonicalHref);
  upsertPropertyMeta("og:title", spec.title);
  upsertPropertyMeta("og:description", spec.description);
  upsertPropertyMeta("og:url", canonicalHref);
  upsertPropertyMeta("og:type", spec.canonicalPath.startsWith("/news/") ? "article" : "website");

  return (): void => {
    document.title = previousTitle;
    upsertNamedMeta("description", previousDescription);
    upsertNamedMeta("robots", previousRobots);
    if (previousCanonical.length > 0) {
      upsertCanonical(previousCanonical);
    }
    upsertPropertyMeta("og:title", previousOgTitle);
    upsertPropertyMeta("og:description", previousOgDescription);
    upsertPropertyMeta("og:url", previousOgUrl);
  };
}
