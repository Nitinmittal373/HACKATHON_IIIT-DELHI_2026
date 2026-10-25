import { notFound, redirect } from "next/navigation";

import { ApiProblem } from "@/components/ApiProblem";
import { AgentCam } from "@/components/cam/AgentCam";
import { ApiError, getCheck } from "@/lib/api";
import { CHECK_ID_PATTERN } from "@/lib/ids";
import type { Check } from "@/lib/types";

interface Props {
  params: Promise<{ id: string }>;
}

export default async function LiveCheckPage({ params }: Props) {
  const { id } = await params;
  if (!CHECK_ID_PATTERN.test(id)) notFound();

  let check: Check;
  try {
    check = await getCheck(id);
  } catch (error) {
    if (!(error instanceof ApiError)) throw error;
    if (error.status === 404) notFound();
    return <ApiProblem error={error} retryHref={`/check/${id}`} />;
  }
  // A finished check has nothing left to watch; its report is the page to open.
  if (check.status === "completed") redirect(`/report/${id}`);

  return <AgentCam checkId={id} reraId={check.rera_id} detailsUrl={check.details_url} />;
}
