const TRUTHY_VALUES: ReadonlySet<string> = new Set(["true", "1", "yes"]);
const FALSY_VALUES: ReadonlySet<string> = new Set(["false", "0", "no"]);

/** Parses a typical env flag; undefined when missing or not a known boolean token. */
export function parseOptionalBooleanEnv(value: string | undefined): boolean | undefined {
  if (value === undefined || value.trim() === "") {
    return undefined;
  }
  const normalized: string = value.trim().toLowerCase();
  if (FALSY_VALUES.has(normalized)) {
    return false;
  }
  if (TRUTHY_VALUES.has(normalized)) {
    return true;
  }
  return undefined;
}
