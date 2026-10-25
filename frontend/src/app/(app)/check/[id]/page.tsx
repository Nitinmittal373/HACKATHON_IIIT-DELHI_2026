import { notFound } from "next/navigation";

import { ResumeCheck } from "@/components/cam/ResumeCheck";
import { CHECK_ID_PATTERN } from "@/lib/ids";

interface Props {
  params: Promise<{ id: string }>;
}

/** The check is loaded in the browser (ResumeCheck), so reopening it resumes where it stands. */
export default async function LiveCheckPage({ params }: Props) {
  const { id } = await params;
  if (!CHECK_ID_PATTERN.test(id)) notFound();
  return <ResumeCheck checkId={id} />;
}
