"use client";

import { Bell, Columns2, FileText, Globe, LayoutDashboard, Menu, MonitorPlay, Plus, ShieldCheck, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { LangToggle, Logo, ThemeToggle } from "@/components/brand";
import { api } from "@/lib/api";
import { useLang, type TKey } from "@/lib/i18n";
import { cn } from "@/lib/utils";

const NAV: { href: string; key: TKey; icon: typeof LayoutDashboard; match: (p: string) => boolean }[] = [
  { href: "/dashboard", key: "app.projects", icon: LayoutDashboard, match: (p) => p === "/dashboard" },
  { href: "/check", key: "app.warroom", icon: MonitorPlay, match: (p) => p.startsWith("/check") },
  { href: "/reports", key: "app.reports", icon: FileText, match: (p) => p.startsWith("/reports") },
  { href: "/compare", key: "app.compare", icon: Columns2, match: (p) => p.startsWith("/compare") },
  { href: "/watch", key: "app.watch", icon: Bell, match: (p) => p.startsWith("/watch") },
];

function NavBody({ onNavigate }: { onNavigate?: () => void }) {
  const path = usePathname();
  const { t } = useLang();
  const [health, setHealth] = useState<{ key_loaded: boolean; demo_mode: boolean } | null | "down">(null);
  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth("down"));
  }, []);
  return (
    <div className="flex h-full flex-col gap-1 px-3.5 py-5">
      <div className="px-2 pb-4"><Logo href="/" size={30} /></div>
      <Link href="/check" onClick={onNavigate} className="mb-3 flex h-11 items-center justify-center gap-2 rounded-xl bg-brand text-sm font-semibold text-[#FFF8F0] transition-colors hover:bg-brand-hover">
        <Plus className="size-4" aria-hidden /> {t("app.newcheck")}
      </Link>
      <div className="px-2.5 pb-1 pt-2 font-mono text-[11px] uppercase tracking-[0.08em] text-faint">Workspace</div>
      <nav aria-label="App" className="flex flex-col gap-0.5">
        {NAV.map(({ href, key, icon: Icon, match }) => {
          const active = match(path);
          return (
            <Link
              key={href}
              href={href}
              onClick={onNavigate}
              aria-current={active ? "page" : undefined}
              className={cn(
                "flex items-center gap-3 rounded-xl px-2.5 py-2.5 text-sm font-medium transition-colors",
                active ? "bg-surface-2 text-fg" : "text-muted hover:bg-surface-2 hover:text-fg",
              )}
            >
              <Icon className="size-[17px]" aria-hidden /> {t(key)}
            </Link>
          );
        })}
      </nav>
      <div className="px-2.5 pb-1 pt-5 font-mono text-[11px] uppercase tracking-[0.08em] text-faint">Trust</div>
      <Link href="/methodology" onClick={onNavigate} className="flex items-center gap-3 rounded-xl px-2.5 py-2.5 text-sm font-medium text-muted hover:bg-surface-2 hover:text-fg">
        <ShieldCheck className="size-[17px]" aria-hidden /> {t("app.method")}
      </Link>
      <Link href="/#faq" onClick={onNavigate} className="flex items-center gap-3 rounded-xl px-2.5 py-2.5 text-sm font-medium text-muted hover:bg-surface-2 hover:text-fg">
        <Globe className="size-[17px]" aria-hidden /> Data sources
      </Link>
      <div className="min-h-6 flex-1" />
      <div className="rounded-xl border border-line p-3 text-xs leading-relaxed text-muted">
        <div className="flex items-center gap-2 text-[13px] font-semibold text-fg">
          <span
            className={cn("size-2 rounded-full", health === "down" ? "bg-[#EF5A4C]" : health && !health.key_loaded ? "bg-[#F2B84B]" : "bg-[#4FC1A6]")}
            aria-hidden
          />
          {health === "down" ? "Backend offline" : health === null ? "Connecting…" : health.demo_mode ? "Demo replay mode" : health.key_loaded ? "Agents ready" : "TinyFish key missing"}
        </div>
        UP-RERA, company registry, IBBI/NCLT, land authorities and news.
      </div>
      <div className="mt-2 flex items-center gap-2 border-t border-line pt-3">
        <LangToggle />
        <div className="flex-1" />
        <ThemeToggle />
      </div>
    </div>
  );
}

export function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <aside className="no-print sticky top-0 hidden h-dvh w-[248px] shrink-0 border-r border-line bg-surface lg:block">
        <NavBody />
      </aside>
      <div className="no-print sticky top-0 z-30 flex items-center justify-between border-b border-line bg-surface px-4 py-3 lg:hidden">
        <Logo href="/" size={28} />
        <button type="button" aria-label="Open menu" aria-expanded={open} onClick={() => setOpen(true)} className="inline-flex size-10 cursor-pointer items-center justify-center rounded-xl border border-line-strong">
          <Menu className="size-5" />
        </button>
      </div>
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Menu">
          <button type="button" aria-label="Close menu" className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-[280px] max-w-[85vw] overflow-y-auto bg-surface shadow-2xl">
            <button type="button" aria-label="Close menu" onClick={() => setOpen(false)} className="absolute right-3 top-4 inline-flex size-9 cursor-pointer items-center justify-center rounded-lg text-muted hover:bg-surface-2">
              <X className="size-5" />
            </button>
            <NavBody onNavigate={() => setOpen(false)} />
          </div>
        </div>
      )}
    </>
  );
}
