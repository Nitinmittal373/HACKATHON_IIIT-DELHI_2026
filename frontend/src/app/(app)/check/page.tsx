import type { Metadata } from "next";

import { BuilderSearch } from "@/components/confirm/BuilderSearch";
import { ProjectSearch } from "@/components/confirm/ProjectSearch";
import { MoreWays } from "@/components/find/MoreWays";
import { CheckCosts } from "@/components/pages/CheckCosts";
import { FeaturedGallery } from "@/components/pages/FeaturedGallery";
import { PageHead } from "@/components/pages/PageHead";
import pages from "@/components/pages/pages.module.css";
import { SearchBar } from "@/components/SearchBar";
import { WakeServer } from "@/components/WakeServer";
import { getStrings } from "@/lib/i18n/server";

type Param = string | string[] | undefined;

interface Props {
  searchParams: Promise<Record<"q" | "locality" | "builder" | "city", Param>>;
}

export async function generateMetadata({ searchParams }: Props): Promise<Metadata> {
  const params = await searchParams;
  if (first(params.q) || first(params.builder)) return { title: "Matching projects · NeevCheck" };
  const { t } = await getStrings();
  return { title: t.pages.check.metaTitle, description: t.pages.check.metaDescription };
}

/**
 * With a query this is the list of matching projects to confirm (the search itself runs in the
 * browser); without one it is the Check a project page.
 */
export default async function CheckPage({ searchParams }: Props) {
  const params = await searchParams;
  const query = first(params.q) ?? "";
  const builder = first(params.builder);
  const city = first(params.city);
  const locality = first(params.locality);
  const { t } = await getStrings();

  if (query.length < 2 && !builder) return <CheckLanding t={t} />;

  return (
    <>
      <div className="eyebrow">{t.confirm.step}</div>
      {/* A new query starts a new search, with fresh state. */}
      {builder ? (
        <BuilderSearch key={`${builder}|${city ?? ""}`} builder={builder} city={city} />
      ) : (
        <ProjectSearch key={`${query}|${locality ?? ""}`} query={query} locality={locality} />
      )}
    </>
  );
}

function CheckLanding({ t }: { t: Awaited<ReturnType<typeof getStrings>>["t"] }) {
  const copy = t.pages.check;
  return (
    <>
      <WakeServer />
      <PageHead title={copy.title} lead={copy.lead} />
      <SearchBar
        align="start"
        label={t.hero.searchLabel}
        placeholder={t.hero.placeholder}
        submitLabel={t.hero.submit}
      />
      <MoreWays align="start" />
      <FeaturedGallery />
      <section className={pages.section} aria-labelledby="reads-title">
        <h2 id="reads-title" className={pages.heading}>
          {copy.readsTitle}
        </h2>
        <ul className={pages.list}>
          {copy.reads.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <p className={pages.text}>{copy.readsNote}</p>
      </section>
      <CheckCosts />
    </>
  );
}

function first(value: Param): string | undefined {
  return (Array.isArray(value) ? value[0] : value)?.trim() || undefined;
}
