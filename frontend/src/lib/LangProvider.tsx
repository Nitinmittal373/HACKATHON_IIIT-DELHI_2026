"use client";

import { useRouter } from "next/navigation";
import { createContext, useContext, useMemo, useState, type ReactNode } from "react";

import { LANG_COOKIE, STRINGS, type Lang, type Strings } from "@/lib/i18n";

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: Strings;
}

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;
const LangContext = createContext<LangState | null>(null);

/** The server reads the cookie and passes it in, so the first paint is already in the right language. */
export function LangProvider({ initial, children }: { initial: Lang; children: ReactNode }) {
  const router = useRouter();
  const [lang, setLangState] = useState<Lang>(initial);

  const value = useMemo<LangState>(() => {
    const setLang = (next: Lang) => {
      setLangState(next);
      document.documentElement.lang = next;
      document.cookie = `${LANG_COOKIE}=${next}; path=/; max-age=${ONE_YEAR_SECONDS}; samesite=lax`;
      // Pages rendered on the server read the cookie too, so ask them to render again.
      router.refresh();
    };
    return { lang, setLang, t: STRINGS[lang] };
  }, [lang, router]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): LangState {
  const state = useContext(LangContext);
  if (!state) throw new Error("useLang must be used inside <LangProvider>");
  return state;
}
