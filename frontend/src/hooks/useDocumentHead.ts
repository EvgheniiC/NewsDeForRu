import { useEffect } from "react";

import { applyDocumentHead } from "../lib/documentHead";
import type { DocumentHeadSpec, RobotsDirective } from "../lib/seo";
import { getPublicAppBaseUrl } from "../lib/shareNews";

/** Keeps document title, robots and Open Graph tags in sync with the current route. */
export function useDocumentHead(spec: DocumentHeadSpec): void {
  const title: string = spec.title;
  const description: string = spec.description;
  const canonicalPath: string = spec.canonicalPath;
  const robots: RobotsDirective = spec.robots;

  useEffect((): (() => void) => {
    return applyDocumentHead({ title, description, canonicalPath, robots }, getPublicAppBaseUrl());
  }, [title, description, canonicalPath, robots]);
}
