const PLACEHOLDER_ORIGIN = "http://same-site.invalid";
// Browsers drop tabs and line breaks inside a URL, so "/<tab>/host" would become "//host".
const CONTROL_CHARACTERS = /[\u0000-\u001f\u007f]/;

/**
 * Where to go after signing in. Only a path on this site is allowed; anything else (another
 * site, a protocol-relative "//host", a backslash trick) falls back to the home page.
 */
export function safeNext(value: string | null | undefined, fallback = "/"): string {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return fallback;
  if (value.includes("\\") || CONTROL_CHARACTERS.test(value)) return fallback;
  try {
    const url = new URL(value, PLACEHOLDER_ORIGIN);
    if (url.origin !== PLACEHOLDER_ORIGIN) return fallback;
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return fallback;
  }
}
