import { AgentDemo } from "@/components/AgentDemo";
import { BrochureVsRecords } from "@/components/BrochureVsRecords";
import { CtaBand } from "@/components/CtaBand";
import { Faq } from "@/components/Faq";
import { Hero } from "@/components/Hero";
import { ScoreScale } from "@/components/ScoreScale";
import { SentinelPhone } from "@/components/SentinelPhone";
import { SourcesMarquee } from "@/components/SourcesMarquee";
import { WakeServer } from "@/components/WakeServer";
import { EXAMPLE_REPORT } from "@/lib/example8334";
import { getStrings } from "@/lib/i18n/server";

/** The home page fetches nothing: its examples are a recorded real check, labelled as such. */
export default async function HomePage() {
  const { t } = await getStrings();
  return (
    <main>
      <WakeServer />
      <Hero report={EXAMPLE_REPORT} />
      <SourcesMarquee label={t.home.marqueeLabel} />
      <BrochureVsRecords report={EXAMPLE_REPORT} t={t} />
      <AgentDemo report={EXAMPLE_REPORT} t={t} />
      <ScoreScale score={EXAMPLE_REPORT.score} t={t} />
      <SentinelPhone project={EXAMPLE_REPORT.shortName} score={EXAMPLE_REPORT.score} t={t} />
      <Faq title={t.home.faq.title} items={t.home.faq.items} />
      <CtaBand t={t} />
    </main>
  );
}
