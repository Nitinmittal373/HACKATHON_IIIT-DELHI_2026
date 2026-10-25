import { AgentDemo } from "@/components/AgentDemo";
import { BrochureVsRecords } from "@/components/BrochureVsRecords";
import { CtaBand } from "@/components/CtaBand";
import { Faq } from "@/components/Faq";
import { Hero } from "@/components/Hero";
import { ScoreScale } from "@/components/ScoreScale";
import { SentinelPhone } from "@/components/SentinelPhone";
import { SourcesMarquee } from "@/components/SourcesMarquee";
import { EXAMPLE_REPORT } from "@/lib/example8334";

/** The home page fetches nothing: its examples are a recorded real check, labelled as such. */
export default function HomePage() {
  return (
    <main>
      <Hero report={EXAMPLE_REPORT} />
      <SourcesMarquee />
      <BrochureVsRecords report={EXAMPLE_REPORT} />
      <AgentDemo report={EXAMPLE_REPORT} />
      <ScoreScale score={EXAMPLE_REPORT.score} />
      <SentinelPhone project={EXAMPLE_REPORT.shortName} score={EXAMPLE_REPORT.score} />
      <Faq />
      <CtaBand />
    </main>
  );
}
