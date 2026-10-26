import type { Metadata } from "next";
import { notFound, redirect } from "next/navigation";
import { cache } from "react";

import { ApiProblem } from "@/components/ApiProblem";
import { PageMessage } from "@/components/PageMessage";
import { ActionPlan } from "@/components/report/ActionPlan";
import { BuilderQuestions } from "@/components/report/BuilderQuestions";
import { ComplaintDraft } from "@/components/report/ComplaintDraft";
import { CorrectionForm } from "@/components/report/CorrectionForm";
import { CreditHeader } from "@/components/report/CreditHeader";
import { DriversCard } from "@/components/report/DriversCard";
import { EvidenceList } from "@/components/report/EvidenceList";
import { FamilyTree } from "@/components/report/FamilyTree";
import { PrintQr } from "@/components/report/PrintQr";
import { SentinelCard } from "@/components/report/SentinelCard";
import { ReportHeader } from "@/components/report/ReportHeader";
import { MethodNote } from "@/components/report/MethodNote";
import { ScoreCard } from "@/components/report/ScoreCard";
import { Timeline } from "@/components/report/Timeline";
import { TrackRecord } from "@/components/report/TrackRecord";
import { ApiError, getReport } from "@/lib/api";
import { dayOf } from "@/lib/format";
import { getStrings } from "@/lib/i18n/server";
import { loadMeta } from "@/lib/meta";
import { CHECK_ID_PATTERN } from "@/lib/ids";
import { evidenceIds } from "@/lib/reportView";
import type { Report } from "@/lib/types";
import styles from "./report.module.css";

interface Props {
  params: Promise<{ id: string }>;
}

// The title and the page both need the report; cache() makes that one request.
const load = cache(async (id: string): Promise<Report | ApiError> => {
  try {
    return await getReport(id);
  } catch (error) {
    if (error instanceof ApiError) return error;
    throw error;
  }
});

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { id } = await params;
  const report = CHECK_ID_PATTERN.test(id) ? await load(id) : null;
  if (!report || report instanceof ApiError) return { title: "NeevCheck report" };
  const name = report.project.name ?? report.project.rera_id;
  return { title: `${name}: NeevScore ${report.display_score.value} · NeevCheck` };
}

export default async function ReportPage({ params }: Props) {
  const { id } = await params;
  if (!CHECK_ID_PATTERN.test(id)) notFound();

  const result = await load(id);
  if (result instanceof ApiError) return failure(result, id);

  const [{ t, lang }, meta] = await Promise.all([getStrings(), loadMeta()]);
  const report = result;
  const ids = evidenceIds(report.findings);
  const readDate = dayOf(report.check.completed_at ?? report.check.started_at, lang);

  return (
    <>
      <ReportHeader report={report} t={t} lang={lang} />
      <div className={styles.grid}>
        <div className={styles.column}>
          <CreditHeader report={report} ids={ids} meta={meta} t={t} />
          <ScoreCard report={report} t={t} />
          <DriversCard report={report} ids={ids} meta={meta} t={t} />
          <EvidenceList report={report} ids={ids} t={t} lang={lang} />
          {report.family && <FamilyTree tree={report.family} />}
        </div>
        <aside className={styles.column}>
          <ActionPlan report={report} t={t} />
          <BuilderQuestions report={report} t={t} />
          <ComplaintDraft report={report} />
          {report.project.promoter && (
            <TrackRecord promoter={report.project.promoter} reraId={report.project.rera_id} />
          )}
          <Timeline events={report.timeline} t={t} lang={lang} />
          <MethodNote report={report} meta={meta} t={t} />
          <SentinelCard project={report.project} t={t} />
          <CorrectionForm reportId={report.check.id} findings={report.findings} />
          <p className={styles.disclaimer}>{t.report.disclaimer(readDate)}</p>
          <PrintQr />
        </aside>
      </div>
    </>
  );
}

async function failure(error: ApiError, id: string) {
  if (error.status === 404) notFound();
  // 409: the check is still running (watch it) or it failed and there is no report.
  if (error.status === 409) {
    const { t } = await getStrings();
    const running = /still running/i.test(error.message);
    if (running) redirect(`/check/${id}`);
    return <PageMessage title={t.cam.failedTitle}>{t.cam.failedBody}</PageMessage>;
  }
  return <ApiProblem error={error} retryHref={`/report/${id}`} />;
}
