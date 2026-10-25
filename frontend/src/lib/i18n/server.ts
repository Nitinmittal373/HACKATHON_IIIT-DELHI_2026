import { cookies } from "next/headers";

import { isLang, LANG_COOKIE, STRINGS, type Lang, type Strings } from "@/lib/i18n";

/** The reader's language, from the cookie the EN / हिं toggle sets. English by default. */
export async function getLang(): Promise<Lang> {
  const saved = (await cookies()).get(LANG_COOKIE)?.value;
  return isLang(saved) ? saved : "en";
}

export async function getStrings(): Promise<{ lang: Lang; t: Strings }> {
  const lang = await getLang();
  return { lang, t: STRINGS[lang] };
}
