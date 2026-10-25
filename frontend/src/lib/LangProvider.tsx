"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import { STRINGS, type Lang, type Strings } from "@/lib/i18n";

interface LangState {
  lang: Lang;
  setLang: (lang: Lang) => void;
  t: Strings;
}

const STORAGE_KEY = "neevcheck-lang";
const LangContext = createContext<LangState | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  // The server always renders English; a saved choice is applied after hydration.
  const [lang, setLangState] = useState<Lang>("en");

  useEffect(() => {
    try {
      const saved = window.localStorage.getItem(STORAGE_KEY);
      if (saved === "en" || saved === "hi") setLangState(saved);
    } catch {
      // Storage can be blocked; the page works without remembering the choice.
    }
  }, []);

  const value = useMemo<LangState>(() => {
    const setLang = (next: Lang) => {
      setLangState(next);
      document.documentElement.lang = next;
      try {
        window.localStorage.setItem(STORAGE_KEY, next);
      } catch {
        // Not remembered, still applied.
      }
    };
    return { lang, setLang, t: STRINGS[lang] };
  }, [lang]);

  return <LangContext.Provider value={value}>{children}</LangContext.Provider>;
}

export function useLang(): LangState {
  const state = useContext(LangContext);
  if (!state) throw new Error("useLang must be used inside <LangProvider>");
  return state;
}
