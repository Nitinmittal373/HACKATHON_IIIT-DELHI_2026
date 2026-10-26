import { redirect } from "next/navigation";

import { BuilderSearch } from "@/components/confirm/BuilderSearch";
import { ProjectSearch } from "@/components/confirm/ProjectSearch";
import { getStrings } from "@/lib/i18n/server";

type Param = string | string[] | undefined;

interface Props {
  searchParams: Promise<Record<"q" | "state" | "locality" | "builder" | "city", Param>>;
}

/** The search itself runs in the browser (ProjectSearch); this page only reads the query. */
export default async function ConfirmPage({ searchParams }: Props) {
  const params = await searchParams;
  const query = first(params.q) ?? "";
  const builder = first(params.builder);
  const city = first(params.city);
  const locality = first(params.locality);
  const state = first(params.state)?.toUpperCase();
  if (query.length < 2 && !builder) redirect("/#search");

  const { t } = await getStrings();
  return (
    <>
      <div className="eyebrow">{t.confirm.step}</div>
      {/* A new query starts a new search, with fresh state. */}
      {builder ? (
        <BuilderSearch key={`${builder}|${city ?? ""}`} builder={builder} city={city} />
      ) : (
        <ProjectSearch
          key={`${query}|${state ?? ""}|${locality ?? ""}`}
          query={query}
          state={state}
          locality={locality}
        />
      )}
    </>
  );
}

function first(value: Param): string | undefined {
  return (Array.isArray(value) ? value[0] : value)?.trim() || undefined;
}
