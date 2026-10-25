import { redirect } from "next/navigation";

import { ProjectSearch } from "@/components/confirm/ProjectSearch";
import { getStrings } from "@/lib/i18n/server";

interface Props {
  searchParams: Promise<{ q?: string | string[] }>;
}

/** The search itself runs in the browser (ProjectSearch); this page only reads the query. */
export default async function ConfirmPage({ searchParams }: Props) {
  const raw = (await searchParams).q;
  const query = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";
  if (query.length < 2) redirect("/#search");

  const { t } = await getStrings();
  return (
    <>
      <div className="eyebrow">{t.confirm.step}</div>
      {/* A new query starts a new search, with fresh state. */}
      <ProjectSearch key={query} query={query} />
    </>
  );
}
