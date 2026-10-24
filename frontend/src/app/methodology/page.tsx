import type { Metadata } from "next";

import { SiteFooter, SiteHeader } from "@/components/site-chrome";
import { Card } from "@/components/ui/primitives";

export const metadata: Metadata = {
  title: "Methodology",
  description: "How NeevScore is calculated: categories, weights, rules, hard stops, confidence and limitations.",
};

const PILLARS = [
  ["P1", "Regulatory compliance (RERA)", "30%", "Registration status, extensions, delay, quarterly progress reports, complaints and orders"],
  ["P2", "Delivery track record", "20%", "The promoter group's other projects: delays and lapsed registrations"],
  ["P3", "Legal & insolvency", "25%", "Insolvency proceedings and their scope, pending cases"],
  ["P4", "Company & financial health", "15%", "Struck-off or liquidated links, lender action, new charges"],
  ["P5", "Land authority & approvals", "5%", "Attributable dues or defaulter records, missing occupancy certificate"],
  ["P6", "News & buyer sentiment", "5%", "Distinct credible reports of delays or protests (signal only)"],
];

const RULES = [
  ["R01", "Registration lapsed or revoked", "P1 = 100 · hard stop", "Official UP-RERA status"],
  ["R02", "Completion date extended", "30 for the first, +20 each after", "Blanket COVID-era force majeure extensions are not counted"],
  ["R03", "Running late", "40 if over 12 months, 70 if over 24", "Revised vs original date on UP-RERA"],
  ["R04", "Progress report not filed", "15 per missing report (last 4)", "Only when the page shows it was due"],
  ["R05", "Complaints or penalty orders", "20 per order + 4 per complaint, max 40", "Complaints are allegations, not findings"],
  ["R06", "Insolvency covering this project or the whole company", "P3 = 100 · hard stop", "Official IBBI/NCLT record with the exact legal name"],
  ["R06S", "Insolvency limited to a different project", "60 · requires review", "Supreme Court has allowed project-wise insolvency"],
  ["R06G", "Verified group company in insolvency", "50", "Official record and verified link"],
  ["R06N", "Insolvency reported in news only", "0 · requires review", "News is a signal, never proof"],
  ["R07", "Struck-off or liquidated links", "40", "Company registry"],
  ["R08", "Land-authority dues", "70", "Official authority page, or news naming the exact legal name"],
  ["R09", "Lender action or new charge (12 months)", "60 SARFAESI, 10 new charge", "A charge alone is a secured loan, not a default"],
  ["R10", "Pending court cases", "5 each, max 40", "Case status and project connection"],
  ["R11", "Adverse news", "10 per distinct story, max 60 · review", "Repeats across outlets count once"],
  ["R12", "Data unavailable", "0", "Lowers confidence, never the score"],
];

export default function MethodologyPage() {
  return (
    <div className="min-h-dvh bg-bg">
      <SiteHeader />
      <main className="mx-auto max-w-[920px] px-6 py-16">
        <div className="font-mono text-[13px] tracking-[0.08em] text-accent">METHODOLOGY · v1.1</div>
        <h1 className="mt-3 text-4xl font-extrabold tracking-tight sm:text-5xl">How NeevScore is calculated</h1>
        <p className="mt-5 text-lg leading-relaxed text-muted">
          NeevScore is a deterministic, evidence-based risk indicator from 300 to 900. Higher means less risk was found
          in the records we checked. An AI model helps read pages; it never decides the score.
        </p>

        <h2 className="mt-14 text-2xl font-bold">The formula</h2>
        <Card className="mt-4 p-6 font-mono text-[15px] leading-8">
          P = Σ (wᵢ × pᵢ)  where pᵢ is the penalty of category i, from 0 to 100<br />
          NeevScore = clip(900 − 6 × P, 300, 900)
        </Card>

        <h2 className="mt-14 text-2xl font-bold">Six categories</h2>
        <Card className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[620px] text-sm">
            <thead><tr className="text-left font-mono text-[11px] uppercase tracking-wider text-faint"><th className="px-5 py-3 font-medium">ID</th><th className="px-5 py-3 font-medium">Category</th><th className="px-5 py-3 font-medium">Weight</th><th className="px-5 py-3 font-medium">Checked</th></tr></thead>
            <tbody>{PILLARS.map((p) => <tr key={p[0]} className="border-t border-line">{p.map((c, i) => <td key={i} className={`px-5 py-3 ${i === 0 || i === 2 ? "font-mono" : ""}`}>{c}</td>)}</tr>)}</tbody>
          </table>
        </Card>

        <h2 className="mt-14 text-2xl font-bold">Worked example</h2>
        <p className="mt-3 text-muted">A project with 3 counted extensions (P1 = 70) whose promoter has insolvency proceedings limited to a different project (P3 = 60):</p>
        <Card className="mt-4 p-6 font-mono text-[14px] leading-8">
          P = 0.30 × 70 + 0.25 × 60 = 21 + 15 = 36<br />
          NeevScore = 900 − 6 × 36 = 684 → Watch<br />
          <span className="text-faint">If the proceedings covered this project, R06 would apply: P = 0.30 × 70 + 0.25 × 100 = 46 → formula 624, hard stop caps it at 449 → High risk</span>
        </Card>

        <h2 className="mt-14 text-2xl font-bold">Bands</h2>
        <ul className="mt-3 list-disc space-y-1.5 pl-6 text-muted">
          <li><b className="text-fg">750–900 Low risk</b>, shown as “Provisional: no red flags yet” when confidence is under 80%</li>
          <li><b className="text-fg">600–749 Watch</b> · <b className="text-fg">450–599 Elevated</b> · <b className="text-fg">300–449 High risk</b></li>
          <li><b className="text-fg">Not enough data</b> when the UP-RERA record could not be read or confidence is under 50%. No number is shown.</li>
        </ul>

        <h2 className="mt-14 text-2xl font-bold">Rules</h2>
        <Card className="mt-4 overflow-x-auto">
          <table className="w-full min-w-[720px] text-sm">
            <thead><tr className="text-left font-mono text-[11px] uppercase tracking-wider text-faint"><th className="px-5 py-3 font-medium">Code</th><th className="px-5 py-3 font-medium">Signal</th><th className="px-5 py-3 font-medium">Penalty</th><th className="px-5 py-3 font-medium">Evidence needed</th></tr></thead>
            <tbody>{RULES.map((r) => <tr key={r[0]} className="border-t border-line align-top">{r.map((c, i) => <td key={i} className={`px-5 py-3 ${i === 0 ? "font-mono text-accent" : i === 3 ? "text-muted" : ""}`}>{c}</td>)}</tr>)}</tbody>
          </table>
        </Card>

        <h2 className="mt-14 text-2xl font-bold">Hard stops</h2>
        <p className="mt-3 leading-relaxed text-muted">
          Two verified events cap the score at 449 and set the band to High risk, whatever the other categories say:
          a lapsed or revoked registration (R01), and insolvency proceedings that cover this project or the whole company (R06).
          Insolvency limited to another project is not a hard stop; it is a heavy penalty marked “requires review”.
          A hard stop needs an official record matching the promoter&apos;s exact legal name. News alone never triggers one.
        </p>

        <h2 className="mt-14 text-2xl font-bold">Evidence and confidence</h2>
        <ul className="mt-3 list-disc space-y-1.5 pl-6 leading-relaxed text-muted">
          <li>No source, no claim. Every claim stores its source URL, an extract and the original retrieval time.</li>
          <li>Each claim is <b className="text-fg">Verified</b> (official source), <b className="text-fg">Partially verified</b> (registry mirror) or <b className="text-fg">Requires review</b> (news or inferred scope).</li>
          <li>Each check is recorded as found, not found in checked records, unavailable, blocked by CAPTCHA or skipped.</li>
          <li>Confidence is the share of seven key signals we could read. Missing data lowers confidence, never the score.</li>
          <li>Matching is strict: “Supertech Limited” never matches “Supertech Realtors”, and “Eco Village I” never matches “Eco Village II”.</li>
          <li>One story repeated by several outlets counts once.</li>
        </ul>

        <h2 className="mt-14 text-2xl font-bold">Limitations and validation plan</h2>
        <p className="mt-3 leading-relaxed text-muted">
          The weights are initial design choices reflecting each category&apos;s likely impact on a buyer. They are not an official
          government formula and are not yet statistically validated. Next steps: test against projects with known outcomes, expert
          review of every rule, sensitivity tests on the weights, and checks for double counting. NeevCheck is decision support, not a
          guarantee of safety or a substitute for legal due diligence.
        </p>
      </main>
      <SiteFooter />
    </div>
  );
}
