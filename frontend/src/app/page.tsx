"use client";

import {
  ArrowRight, Bell, Building2, Columns2, Eye, FileText, Globe, Home, Landmark, Link2, MessageSquareText,
  MonitorPlay, Network, Search, ShieldCheck,
} from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { BandBadge, ScoreGauge } from "@/components/score";
import { Reveal, SectionHead, SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Button } from "@/components/ui/button";
import { Badge, Card, Input } from "@/components/ui/primitives";
import { useLang } from "@/lib/i18n";

const SOURCES = ["UP-RERA project records", "Quarterly progress reports", "MCA company data", "IBBI insolvency", "NCLT orders", "Noida Authority", "Greater Noida Authority", "YEIDA", "News & buyer protests"];

const FAQ = [
  ["Is NeevCheck a credit rating or legal advice?", "No. It is a risk indicator built from public records. It tells you what the records say, links each fact to its source, and marks what still needs checking. Verify the sources and talk to a lawyer before you decide."],
  ["How is the score calculated?", "A fixed formula, not an AI guess. Six risk categories have published weights. Each finding adds a documented penalty, and NeevScore = 900 − 6 × the weighted penalty, kept between 300 and 900. Every report shows the calculation, so you can reproduce it."],
  ["Where does the data come from?", "UP-RERA project records and progress reports, company data from the MCA registry, IBBI and NCLT insolvency records, land-authority notices and news. Each claim carries its source link and the date we retrieved it."],
  ["What if a government site is down?", "That source is marked unavailable and confidence drops. Missing data never raises or lowers the score by itself, and if UP-RERA itself can't be read we show “Not enough data” instead of a score."],
  ["Is a news article treated as proof?", "No. News is shown as “requires review” and adds no insolvency penalty on its own. Hard stops need an official record that matches the company's exact legal name."],
  ["Do your agents log in anywhere or solve CAPTCHAs?", "No. Agents read public pages only, the same pages you could open yourself. They never log in and never solve CAPTCHAs automatically."],
  ["Which cities do you cover?", "Uttar Pradesh today, including Noida, Greater Noida and the YEIDA region. Each new state is a new source adapter on the same data model."],
  ["What do you store about me?", "Only the projects you check or watch. We never ask for Aadhaar, PAN or bank details."],
];

export default function Landing() {
  const { t, lang } = useLang();
  const router = useRouter();
  const [q, setQ] = useState("");
  const go = (query: string) => router.push(query.trim().length >= 3 ? `/check?q=${encodeURIComponent(query.trim())}` : "/check");

  return (
    <div className="bg-dots min-h-dvh bg-bg">
      <SiteHeader />

      {/* HERO */}
      <section className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-14 px-6 pb-20 pt-16 sm:pt-24">
        <div className="min-w-0 flex-[1_1_520px]">
          <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="inline-flex items-center gap-2.5 rounded-full border border-line-strong bg-surface py-1.5 pl-2 pr-3.5 text-[13px] text-fg-2">
            <span className="rounded-full bg-ok-bg px-2 py-0.5 font-mono text-[11px] font-semibold text-ok-fg">LIVE</span>
            {t("hero.badge")}
          </motion.div>
          <motion.h1
            key={lang}
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="mt-6 text-balance text-5xl font-extrabold leading-[1.04] tracking-[-0.045em] sm:text-[68px]"
          >
            {t("hero.title")}
          </motion.h1>
          <p className="mt-6 max-w-[560px] text-lg leading-relaxed text-muted sm:text-[19px]">{t("hero.sub")}</p>
          <form onSubmit={(e) => { e.preventDefault(); go(q); }} className="mt-8 flex max-w-[600px] flex-wrap gap-2.5 rounded-2xl border border-line-strong bg-surface p-2 shadow-[0_20px_50px_-30px_var(--shadow)]">
            <div className="flex min-w-0 flex-[1_1_260px] items-center gap-2.5 px-3">
              <Search className="size-5 text-faint" aria-hidden />
              <label htmlFor="hero-q" className="sr-only">{t("hero.placeholder")}</label>
              <Input id="hero-q" value={q} onChange={(e) => setQ(e.target.value)} maxLength={160} placeholder={t("hero.placeholder")} className="h-12 text-base" />
            </div>
            <Button type="submit" size="lg">{t("cta.run")}</Button>
          </form>
          <div className="mt-3.5 flex flex-wrap items-center gap-2 text-[13px] text-faint">
            <span>Try:</span>
            {["Supertech Eco Village", "Builder name", "UPRERAPRJ…"].map((x) => (
              <button key={x} type="button" onClick={() => (x.endsWith("…") || x === "Builder name" ? setQ("") : go(x))} className="cursor-pointer rounded-full border border-line-strong px-3 py-1 text-fg-2 transition-colors hover:border-accent">{x}</button>
            ))}
          </div>
        </div>

        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.15 }} className="relative min-w-0 max-w-[460px] flex-[1_1_380px]">
          <div className="animate-float">
            <Card className="rounded-3xl p-6 shadow-[0_40px_80px_-30px_var(--shadow)]">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="font-mono text-[11px] tracking-[0.06em] text-faint">EXAMPLE · PUBLIC RECORDS</div>
                  <div className="mt-1 font-semibold">Supertech Eco Village I</div>
                </div>
                <Badge tone="info">Formula v1.1</Badge>
              </div>
              <div className="mt-4"><ScoreGauge score={684} band="Watch" /></div>
              <div className="mt-3 flex flex-wrap justify-center gap-2"><BandBadge band="Watch" /><Badge>No hard stop</Badge></div>
              <div className="mt-5 flex flex-col gap-2.5 text-sm">
                <div className="flex gap-3 rounded-xl border border-warn-line bg-warn-soft p-3">
                  <span className="font-mono text-xs text-warn-fg">R06S</span>
                  <span>Promoter&apos;s insolvency is limited to a different project. <span className="text-warn-fg">Requires review</span></span>
                </div>
                <div className="flex gap-3 rounded-xl border border-line bg-surface-2 p-3">
                  <span className="font-mono text-xs text-warn-fg">R02</span>
                  <span>Completion date extended 3 times on UP-RERA</span>
                </div>
              </div>
              <div className="mt-4 rounded-xl bg-surface-3 px-3 py-2 font-mono text-[11.5px] text-muted">900 − 6 × (0.30×70 + 0.25×60) = 684</div>
            </Card>
          </div>
          <div className="absolute -bottom-5 -left-4 flex items-center gap-2.5 rounded-2xl border border-line-strong bg-surface px-3.5 py-3 text-[13px] shadow-[0_20px_40px_-20px_var(--shadow)] sm:-left-7">
            <Link2 className="size-4 text-ok-fg" aria-hidden /> Every claim <b>links to its source</b>
          </div>
        </motion.div>
      </section>

      {/* SOURCES */}
      <section aria-label="Sources NeevCheck reads" className="overflow-hidden border-y border-line bg-bg-2 py-5">
        <div className="flex w-max animate-marquee gap-14 font-mono text-sm uppercase tracking-[0.04em] text-faint">
          {[...SOURCES, ...SOURCES].map((s, i) => <span key={i} className="flex items-center gap-14">{s}<span aria-hidden>·</span></span>)}
        </div>
      </section>

      {/* PROBLEM */}
      <section className="mx-auto max-w-[1200px] px-6 pt-28">
        <SectionHead eyebrow="THE PROBLEM" title="A home is the biggest cheque most families sign. The warning signs are public, but scattered across government sites." />
        <div className="mt-12 grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
          {[
            ["5+ portals", "RERA, MCA, IBBI, NCLT and three land authorities, each with its own search and its own CAPTCHA."],
            ["Hours of digging", "Most buyers rely on the brochure and the broker, because checking the records properly is a lawyer's job."],
            ["Risk keeps changing", "A project that looks fine at booking can miss filings or face insolvency a year later. Nobody tells the buyer."],
          ].map(([h, p], i) => (
            <Reveal key={h} delay={i * 0.08}><Card className="h-full p-7"><div className="text-[28px] font-bold tracking-tight">{h}</div><p className="mt-2.5 leading-relaxed text-muted">{p}</p></Card></Reveal>
          ))}
        </div>
      </section>

      {/* HOW */}
      <section id="how" className="mx-auto max-w-[1200px] scroll-mt-24 px-6 pt-28">
        <SectionHead eyebrow="HOW IT WORKS" title="Type a name. Watch the agents work. Get a score you can check." />
        <div className="mt-12 grid grid-cols-[repeat(auto-fit,minmax(290px,1fr))] gap-4">
          {[
            [Search, "Find the official record", "Project name, UP-RERA number or builder. Search locates the exact UP-RERA page first."],
            [MonitorPlay, "Five lanes, in parallel", "Web agents read RERA and company pages; Search covers insolvency, land dues and news. Watch each browser live."],
            [ShieldCheck, "One explainable score", "NeevScore from 300 to 900 with reason codes, evidence status and a source for every claim."],
          ].map(([Icon, h, p], i) => {
            const I = Icon as typeof Search;
            return (
              <Reveal key={h as string} delay={i * 0.08}>
                <Card className="h-full p-7 transition-all hover:-translate-y-1 hover:border-line-strong">
                  <div className="flex items-center justify-between"><span className="font-mono text-faint">0{i + 1}</span><I className="size-6 text-accent" aria-hidden /></div>
                  <h3 className="mt-6 text-[22px] font-semibold tracking-tight">{h as string}</h3>
                  <p className="mt-2.5 leading-relaxed text-muted">{p as string}</p>
                </Card>
              </Reveal>
            );
          })}
        </div>
      </section>

      {/* TINYFISH */}
      <section className="mx-auto max-w-[1200px] px-6 pt-28">
        <Reveal>
          <Card className="rounded-[28px] bg-bg-2 p-8 sm:p-10">
            <div className="flex flex-wrap items-end justify-between gap-5">
              <div className="max-w-2xl">
                <div className="font-mono text-[13px] tracking-[0.08em] text-accent">UNDER THE HOOD</div>
                <h2 className="mt-3 text-3xl font-bold leading-tight tracking-tight sm:text-4xl">Built on four TinyFish tools, each doing the job it is best at.</h2>
              </div>
              <p className="max-w-sm leading-relaxed text-muted">Free tools find and read pages first. Paid agents are used only where a page needs clicking.</p>
            </div>
            <div className="mt-8 grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-3.5">
              {[
                ["SEARCH", "Finds the record", "Locates the exact UP-RERA page, company page and insolvency orders."],
                ["FETCH", "Reads simple pages", "Pulls text from notices and articles without spending agent time."],
                ["WEB AGENTS", "Clicks through portals", "Opens project tabs and progress reports and returns structured data, streamed live."],
                ["MONITOR", "Watches for changes", "Rechecks watched projects every morning and calls our webhook when a record changes."],
              ].map(([k, h, p]) => (
                <Card key={k} className="p-5 transition-all hover:-translate-y-1"><div className="font-mono text-xs text-accent">{k}</div><div className="mt-2.5 text-[17px] font-semibold">{h}</div><p className="mt-1.5 text-sm leading-relaxed text-muted">{p}</p></Card>
              ))}
            </div>
          </Card>
        </Reveal>
      </section>

      {/* FEATURES */}
      <section className="mx-auto max-w-[1200px] px-6 pt-28">
        <SectionHead eyebrow="WHAT YOU GET" title="Before you book, and every month after." />
        <div className="mt-12 grid grid-cols-[repeat(auto-fit,minmax(330px,1fr))] gap-4">
          <Feature icon={MonitorPlay} title="Live War Room" text="See each agent's steps and browser as it works, not a spinner.">
            <div className="relative mt-5 overflow-hidden rounded-xl border border-line-strong bg-surface-3 p-4 font-mono text-[13px] leading-8 text-muted">
              <div className="absolute inset-x-0 h-0.5 animate-scan bg-accent/50" />
              <div><span className="text-ok-fg">✓</span> UP-RERA · project record read</div>
              <div><span className="text-ok-fg">✓</span> Company · exact name matched</div>
              <div><span className="text-warn-fg">●</span> NCLT · checking scope of order…</div>
              <div className="text-faint">○ Land authority · queued</div>
            </div>
          </Feature>
          <Feature icon={FileText} title="Evidence with a status" text="Every claim is Verified, Partially verified or Requires review, with the source and retrieval date.">
            <div className="mt-5 flex flex-col gap-2 text-[13px]">
              {[["Registration record", "Verified", "ok"], ["Company status", "Partially verified", "info"], ["News report", "Requires review", "warn"]].map(([a, b, tone]) => (
                <div key={a} className="flex items-center justify-between gap-3 rounded-xl border border-line px-3 py-2.5"><span>{a}</span><Badge tone={tone as "ok"}>{b}</Badge></div>
              ))}
            </div>
          </Feature>
          <Feature icon={Network} title="Builder family tree" text="Promoters often run several companies. We draw the links and mark which are official and which still need checking." />
          <Feature icon={MessageSquareText} title="Ask about your report" text="Plain-language answers built only from the evidence, with citation numbers. If the evidence doesn't cover it, we say so." />
          <Feature icon={Bell} title="Watch mode" text="Daily rechecks. You hear from us when a filing is missed, a date moves or a new court order names your builder." />
          <Feature icon={Columns2} title="Compare projects" text="Shortlisted two homes? Same formula, same sources, side by side." />
          <Feature icon={FileText} title="Complaint draft & PDF" text="A UP-RERA complaint draft from verified facts, and the full dossier as a PDF." />
          <Feature icon={Globe} title="English and हिंदी" text="Key screens read in Hindi too, so parents and first-time buyers can follow." />
        </div>
      </section>

      {/* DIFFERENT */}
      <section className="mx-auto max-w-[1200px] px-6 pt-28">
        <SectionHead eyebrow="WHY TRUST IT" title="Other tools put records in one place. We show our working." sub="Several services already offer RERA search, builder history or alerts. NeevCheck is built around evidence you can check and a score you can reproduce." />
        <div className="mt-12 grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
          {[
            ["A formula you can reproduce", "Weights, rules and the calculation are on every report."],
            ["A status on every claim", "Verified, partially verified or requires review. Allegations are never shown as facts."],
            ["Gaps shown, not hidden", "“Not found in checked records” is not “does not exist”. Missing data lowers confidence, not the score."],
            ["Live, not stale", "Agents read today's records while you watch, then Monitor keeps checking."],
          ].map(([h, p], i) => (
            <Reveal key={h} delay={i * 0.06}><div className="h-full border-t-2 border-accent pt-5"><h3 className="text-lg font-semibold">{h}</h3><p className="mt-2 leading-relaxed text-muted">{p}</p></div></Reveal>
          ))}
        </div>
      </section>

      {/* SCORE */}
      <section id="score" className="mx-auto max-w-[1200px] scroll-mt-24 px-6 pt-28">
        <div className="flex flex-wrap gap-12">
          <div className="min-w-0 flex-[1_1_380px]">
            <SectionHead eyebrow="NEEVSCORE" title="Like a credit score, but for your builder." sub="A fixed formula decides the score. The same records always give the same number, and you can see exactly which category pulled it down." />
            <Reveal className="mt-8">
              <div className="flex h-3.5 overflow-hidden rounded-full">
                <div className="flex-1 bg-[#EF5A4C]" /><div className="flex-1 bg-[#F08A4B]" /><div className="flex-1 bg-[#F2B84B]" /><div className="flex-1 bg-[#4FC1A6]" />
              </div>
              <div className="mt-2.5 flex justify-between font-mono text-xs text-faint"><span>300</span><span>450</span><span>600</span><span>750</span><span>900</span></div>
              <div className="mt-1.5 grid grid-cols-4 text-[13px] text-fg-2"><span>High risk</span><span>Elevated</span><span>Watch</span><span>Low risk</span></div>
              <div className="mt-7 flex items-center gap-4 rounded-2xl border border-dashed border-line-strong p-4">
                <div className="w-10 text-center text-3xl font-extrabold text-faint">–</div>
                <div><div className="font-semibold">Not enough data</div><div className="mt-0.5 text-sm text-muted">Shown when a key source can&apos;t be read. We never show a safe score we can&apos;t back.</div></div>
              </div>
            </Reveal>
          </div>
          <Reveal className="min-w-0 flex-[1_1_460px]">
            <Card className="p-7">
              <div className="font-semibold">Six categories, fixed weights</div>
              <div className="mt-5 flex flex-col gap-4 text-sm">
                {[["Regulatory compliance (RERA)", 30], ["Legal & insolvency", 25], ["Delivery track record", 20], ["Company & financial health", 15], ["Land authority & approvals", 5], ["News & buyer sentiment", 5]].map(([n, w]) => (
                  <div key={n as string}>
                    <div className="flex justify-between"><span>{n}</span><span className="font-mono">{w}%</span></div>
                    <div className="mt-2 h-2 overflow-hidden rounded-full bg-track">
                      <motion.div className="h-full rounded-full bg-accent" initial={{ width: 0 }} whileInView={{ width: `${(w as number) / 0.3}%` }} viewport={{ once: true }} transition={{ duration: 1.2 }} />
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-6 rounded-xl bg-surface-3 p-4 font-mono text-[13px] leading-7 text-fg-2">
                NeevScore = clip(900 − 6 × Σ wᵢ·pᵢ, 300, 900)<br />
                Hard stop: lapsed registration, or insolvency that covers this project → capped at 449
              </div>
              <Link href="/methodology" className="mt-4 inline-flex items-center gap-1.5 text-sm font-semibold text-accent hover:underline">Read the full methodology <ArrowRight className="size-4" /></Link>
            </Card>
          </Reveal>
        </div>
      </section>

      {/* AUDIENCE */}
      <section className="mx-auto max-w-[1200px] px-6 pt-28">
        <SectionHead eyebrow="WHO IT'S FOR" title="For the buyer first. Built to plug into everyone else." />
        <div className="mt-12 grid grid-cols-[repeat(auto-fit,minmax(300px,1fr))] gap-4">
          <Feature icon={Home} title="Homebuyers" text="Check a project before paying the booking amount, then keep watching it until possession." />
          <Feature icon={Globe} title="NRIs buying from abroad" text="See the record without a site visit, and share the report link with family in India." />
          <Feature icon={Landmark} title="Lenders, brokers & portals" text="One API call returns the score, reasons and evidence for any project in their listings.">
            <pre className="mt-4 overflow-x-auto rounded-xl border border-line bg-surface-3 p-3 font-mono text-xs leading-6 text-fg-2">{`POST /api/investigations
{ "query": "UPRERAPRJ…" }
GET  /api/reports/{id}
→ score, reasons[], evidence[]`}</pre>
          </Feature>
        </div>
      </section>

      {/* COVERAGE */}
      <section className="mx-auto max-w-[1200px] px-6 pt-28">
        <div className="flex flex-wrap gap-10">
          <div className="min-w-0 flex-[1_1_360px]">
            <SectionHead eyebrow="COVERAGE" title="Starting with Uttar Pradesh." sub="Each new state is a source adapter mapped to the same data model. The scoring and evidence rules stay the same." />
          </div>
          <Reveal className="flex min-w-0 flex-[1_1_480px] flex-col gap-2.5">
            {[["Uttar Pradesh · Noida, Greater Noida, YEIDA", "Live"], ["Haryana · Gurugram", "Next"], ["Maharashtra · Mumbai, Pune", "Next"], ["Karnataka · Bengaluru", "Next"]].map(([s, st]) => (
              <Card key={s} className="flex items-center justify-between gap-3 rounded-xl px-5 py-4">
                <span className={st === "Live" ? "font-semibold" : ""}><Building2 className="mr-2 inline size-4 text-faint" aria-hidden />{s}</span>
                <Badge tone={st === "Live" ? "ok" : "neutral"}>{st}</Badge>
              </Card>
            ))}
          </Reveal>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="mx-auto max-w-[900px] scroll-mt-24 px-6 pt-28">
        <SectionHead eyebrow="FAQ" title="Questions buyers ask us" center />
        <Reveal className="mt-10">
          <Card className="overflow-hidden">
            <Accordion type="single" collapsible defaultValue="0">
              {FAQ.map(([q, a], i) => (
                <AccordionItem key={q} value={String(i)}>
                  <AccordionTrigger>{q}</AccordionTrigger>
                  <AccordionContent>{a}</AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          </Card>
        </Reveal>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-[1200px] px-6 py-28">
        <Reveal>
          <Card className="rounded-[28px] bg-bg-2 px-8 py-16 text-center">
            <h2 className="text-balance text-4xl font-extrabold tracking-tight sm:text-5xl">Check before you pay the booking amount.</h2>
            <p className="mx-auto mt-4 max-w-xl text-lg text-muted">About two minutes. Every claim sourced. Every gap shown.</p>
            <div className="mt-8 flex flex-wrap justify-center gap-3">
              <Button asChild size="lg"><Link href="/check">{t("cta.run")} <ArrowRight /></Link></Button>
              <Button asChild size="lg" variant="outline"><Link href="/dashboard"><Eye /> Open the app</Link></Button>
            </div>
          </Card>
        </Reveal>
      </section>

      <SiteFooter />
    </div>
  );
}

function Feature({ icon: Icon, title, text, children }: { icon: typeof Search; title: string; text: string; children?: React.ReactNode }) {
  return (
    <Reveal>
      <Card className="h-full p-7 transition-all hover:-translate-y-1 hover:border-line-strong">
        <div className="flex items-center gap-3"><Icon className="size-6 text-accent" aria-hidden /><h3 className="text-[21px] font-semibold tracking-tight">{title}</h3></div>
        <p className="mt-2.5 leading-relaxed text-muted">{text}</p>
        {children}
      </Card>
    </Reveal>
  );
}
