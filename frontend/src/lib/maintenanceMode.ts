import { Capacitor } from "@capacitor/core";

import { parseOptionalBooleanEnv } from "./envFlags";

const LEGAL_PATHS: ReadonlySet<string> = new Set(["/privacy", "/contact", "/impressum"]);

export interface MaintenanceModeOptions {
  readonly isNative: boolean;
  readonly isProd: boolean;
  readonly envValue: string | undefined;
}

/** Parses VITE_MAINTENANCE_MODE; production web builds are closed until explicitly reopened. */
export function resolveMaintenanceMode(options: MaintenanceModeOptions): boolean {
  if (options.isNative) {
    return false;
  }

  const parsed: boolean | undefined = parseOptionalBooleanEnv(options.envValue);
  if (parsed !== undefined) {
    return parsed;
  }

  return options.isProd;
}

/** True when the public web site should show the reconstruction page. */
export function isMaintenanceMode(): boolean {
  return resolveMaintenanceMode({
    isNative: Capacitor.isNativePlatform(),
    isProd: import.meta.env.PROD,
    envValue: import.meta.env.VITE_MAINTENANCE_MODE,
  });
}

/** Legal pages and staff/auth routes stay reachable while the public feed is closed. */
export function isMaintenanceExemptPath(pathname: string): boolean {
  if (LEGAL_PATHS.has(pathname)) {
    return true;
  }
  return pathname === "/login" || pathname.startsWith("/account") || pathname.startsWith("/moderation");
}
