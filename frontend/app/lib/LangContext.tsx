"use client";

import { createContext, useContext, useState, useEffect, type ReactNode } from "react";
import { type Lang, type Translations, getTranslations, detectBrowserLang } from "./i18n";

interface LangContextValue {
  lang: Lang;
  t: Translations;
  toggleLang: () => void;
}

const LangContext = createContext<LangContextValue | null>(null);

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>("en");

  useEffect(() => {
    const saved = localStorage.getItem("aoe4bot_lang") as Lang | null;
    setLang(saved || detectBrowserLang());
  }, []);

  const toggleLang = () => {
    const next = lang === "en" ? "es" : "en";
    setLang(next);
    localStorage.setItem("aoe4bot_lang", next);
  };

  const t = getTranslations(lang);

  return (
    <LangContext.Provider value={{ lang, t, toggleLang }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  const ctx = useContext(LangContext);
  if (!ctx) throw new Error("useLang must be used within LangProvider");
  return ctx;
}
