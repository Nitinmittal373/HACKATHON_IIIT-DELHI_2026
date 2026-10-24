"use client";

import { ArrowRight } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import type { ReactNode } from "react";

import { LangToggle, Logo, ThemeToggle } from "@/components/brand";
import { Button } from "@/components/ui/button";
import { useLang } from "@/lib/i18n";

export function SiteHeader() {
  const { t } = useLang();
  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/80 backdrop-blur-xl">
      <nav aria-label="Main" className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-x-6 gap-y-3 px-5 py-3.5 sm:px-6">
        <Logo />
        <div className="order-3 flex w-full flex-wrap gap-5 text-sm md:order-none md:w-auto md:flex-1">
          <Link className="text-muted hover:text-fg" href="/#how">{t("nav.how")}</Link>
          <Link className="text-muted hover:text-fg" href="/#score">{t("nav.score")}</Link>
          <Link className="text-muted hover:text-fg" href="/methodology">{t("nav.method")}</Link>
          <Link className="text-muted hover:text-fg" href="/#faq">{t("nav.faq")}</Link>
        </div>
        <div className="ml-auto flex items-center gap-2 md:ml-0">
          <LangToggle className="hidden sm:flex" />
          <ThemeToggle />
          <Button asChild variant="outline" size="sm" className="hidden sm:inline-flex"><Link href="/dashboard">{t("nav.app")}</Link></Button>
          <Button asChild size="sm"><Link href="/check">{t("cta.check")} <ArrowRight /></Link></Button>
        </div>
      </nav>
    </header>
  );
}

export function SiteFooter() {
  const { t } = useLang();
  return (
    <footer className="border-t border-line">
      <div className="mx-auto flex max-w-[1200px] flex-wrap justify-between gap-10 px-6 py-12 text-sm leading-7 text-faint">
        <div className="max-w-sm">
          <Logo />
          <p className="mt-3">{t("disclaimer")} Always verify with the original source before you decide.</p>
        </div>
        <div className="flex flex-wrap gap-14">
          <div className="flex flex-col"><span className="font-semibold text-fg">Product</span><Link className="hover:text-fg" href="/check">Run a check</Link><Link className="hover:text-fg" href="/compare">Compare</Link><Link className="hover:text-fg" href="/watch">Watch mode</Link></div>
          <div className="flex flex-col"><span className="font-semibold text-fg">Trust</span><Link className="hover:text-fg" href="/methodology">Methodology</Link><Link className="hover:text-fg" href="/#faq">Data sources</Link><Link className="hover:text-fg" href="/#faq">Privacy</Link></div>
          <div className="flex flex-col"><span className="font-semibold text-fg">Team RYZEN</span><span>KIET Group of Institutions</span><span>HackIIITD 2026</span><span>Powered by TinyFish</span></div>
        </div>
      </div>
    </footer>
  );
}

/** Fade-and-rise on scroll. Respects reduced motion through the global CSS rule. */
export function Reveal({ children, delay = 0, className }: { children: ReactNode; delay?: number; className?: string }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 18 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-60px" }}
      transition={{ duration: 0.55, delay, ease: [0.2, 0.8, 0.2, 1] }}
    >
      {children}
    </motion.div>
  );
}

export function SectionHead({ eyebrow, title, sub, center }: { eyebrow: string; title: string; sub?: string; center?: boolean }) {
  return (
    <Reveal className={center ? "mx-auto max-w-3xl text-center" : "max-w-3xl"}>
      <div className="font-mono text-[13px] tracking-[0.08em] text-accent">{eyebrow}</div>
      <h2 className="mt-3.5 text-balance text-4xl font-bold leading-[1.1] tracking-tight sm:text-[46px]">{title}</h2>
      {sub && <p className="mt-4 text-lg leading-relaxed text-muted">{sub}</p>}
    </Reveal>
  );
}
