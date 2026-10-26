import { AgentDemo } from "@/components/AgentDemo";
import { BrochureVsRecords } from "@/components/BrochureVsRecords";
import { CtaBand } from "@/components/CtaBand";
import { Faq } from "@/components/Faq";
import { Hero } from "@/components/Hero";
import { RecentStrip } from "@/components/RecentStrip";
import { ScoreScale } from "@/components/ScoreScale";
import { SentinelPhone } from "@/components/SentinelPhone";
import { SourcesMarquee } from "@/components/SourcesMarquee";
import { WakeServer } from "@/components/WakeServer";
import { EXAMPLE_REPORT } from "@/lib/example8334";
import { getStrings } from "@/lib/i18n/server";

/**
 * The hero card and the strip below it show real finished checks, fetched in the browser. The
 * sections further down illustrate with one recorded real check, and say so.
 */
export default async function HomePage() {
  const { t } = await getStrings();
  return (
    <main>
      <WakeServer />
      <Hero />
      <RecentStrip />
      <SourcesMarquee label={t.home.marqueeLabel} />
      <BrochureVsRecords report={EXAMPLE_REPORT} t={t} />
      <AgentDemo report={EXAMPLE_REPORT} t={t} />
      <ScoreScale />
      <SentinelPhone project={EXAMPLE_REPORT.shortName} score={EXAMPLE_REPORT.score} t={t} />
      <Faq title={t.home.faq.title} items={t.home.faq.items} />
      <CtaBand t={t} />
    </main>
  );
}
