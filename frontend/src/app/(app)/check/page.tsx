import Link from "next/link";
import { redirect } from "next/navigation";

import { PageMessage } from "@/components/PageMessage";
import { ConfirmPicker } from "@/components/confirm/ConfirmPicker";
import { EmptyResults } from "@/components/confirm/EmptyResults";
import { ApiError, searchProjects } from "@/lib/api";
import { getStrings } from "@/lib/i18n/server";
import type { SearchResponse } from "@/lib/types";

interface Props {
  searchParams: Promise<{ q?: string | string[] }>;
}

async function find(query: string): Promise<SearchResponse | ApiError> {
  try {
    return await searchProjects(query);
  } catch (error) {
    return error instanceof ApiError ? error : new ApiError("The search failed", 502);
  }
}

export default async function ConfirmPage({ searchParams }: Props) {
  const raw = (await searchParams).q;
  const query = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";
  if (query.length < 2) redirect("/#search");

  const { t } = await getStrings();
  const result = await find(query);
  const step = <div className="eyebrow">{t.confirm.step}</div>;

  if (result instanceof ApiError) {
    const unreachable = result.status === 0;
    return (
      <>
        {step}
        <PageMessage
          alert
          title={unreachable ? t.errors.unreachableTitle : t.confirm.searchFailedTitle}
          actions={
            <Link href={`/check?q=${encodeURIComponent(query)}`} className="btn">
              {t.common.tryAgain}
            </Link>
          }
        >
          {unreachable ? t.errors.unreachableBody : t.confirm.searchFailedBody}
        </PageMessage>
      </>
    );
  }

  if (result.candidates.length === 0) {
    return (
      <>
        {step}
        <EmptyResults query={query} t={t} />
      </>
    );
  }

  return (
    <>
      {step}
      <h1 className="h2 pageTitle">{t.confirm.title(result.candidates.length, query)}</h1>
      <p className="pageLead">{t.confirm.lead}</p>
      <ConfirmPicker projects={result.candidates} />
    </>
  );
}
