"use client";

import { Moon, Sun } from "lucide-react";
import Link from "next/link";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import { useLang } from "@/lib/i18n";
import { cn } from "@/lib/utils";

export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 120 120" aria-hidden>
      <rect width="120" height="120" rx="30" fill="#B4481A" />
      <path d="M26 60 L60 30 L94 60" fill="none" stroke="#FFF8F0" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M43 68 L55 80 L78 56" fill="none" stroke="#FFF8F0" strokeWidth="10" strokeLinecap="round" strokeLinejoin="round" />
      <rect x="26" y="90" width="68" height="9" rx="4.5" fill="#FFF8F0" />
    </svg>
  );
}

export function Logo({ href = "/", size = 32 }: { href?: string; size?: number }) {
  return (
    <Link href={href} className="flex items-center gap-2.5 text-fg" aria-label="NeevCheck home">
      <LogoMark size={size} />
      <span className="text-lg font-bold tracking-tight">NeevCheck</span>
    </Link>
  );
}

export function ThemeToggle({ className }: { className?: string }) {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const dark = !mounted || resolvedTheme === "dark";
  return (
    <button
      type="button"
      onClick={() => setTheme(dark ? "light" : "dark")}
      aria-label={dark ? "Switch to light mode" : "Switch to dark mode"}
      className={cn(
        "inline-flex size-10 cursor-pointer items-center justify-center rounded-full border border-line-strong bg-surface text-fg transition-colors hover:bg-surface-2",
        className,
      )}
    >
      {dark ? <Sun className="size-[17px]" aria-hidden /> : <Moon className="size-[17px]" aria-hidden />}
    </button>
  );
}

export function LangToggle({ className }: { className?: string }) {
  const { lang, setLang } = useLang();
  return (
    <div role="group" aria-label="Language" className={cn("flex rounded-full border border-line-strong bg-surface p-[3px]", className)}>
      {(["en", "hi"] as const).map((l) => (
        <button
          key={l}
          type="button"
          aria-pressed={lang === l}
          onClick={() => setLang(l)}
          className={cn(
            "cursor-pointer rounded-full px-3 py-1.5 text-[13px] font-semibold transition-colors",
            lang === l ? "bg-fg text-bg" : "text-muted hover:text-fg",
          )}
        >
          {l === "en" ? "EN" : "हिं"}
        </button>
      ))}
    </div>
  );
}
