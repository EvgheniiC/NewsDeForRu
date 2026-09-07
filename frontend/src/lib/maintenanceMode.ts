import { Capacitor } from "@capacitor/core";

const TRUTHY_VALUES: ReadonlySet<string> = new Set(["true", "1", "yes"]);
const FALSY_VALUES: ReadonlySet<string> = new Set(["false", "0", "no"]);

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

  if (options.envValue !== undefined && options.envValue.trim() !== "") {
    const normalized: string = options.envValue.trim().toLowerCase();
    if (FALSY_VALUES.has(normalized)) {
      return false;
    }
    if (TRUTHY_VALUES.has(normalized)) {
      return true;
    }
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
