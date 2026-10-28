import type { Metadata } from "next";

import { PageHead } from "@/components/pages/PageHead";
import styles from "@/components/pages/pages.module.css";
import { RwaSignIn } from "@/components/pages/RwaSignIn";
import { Steps } from "@/components/pages/Steps";
import { getStrings } from "@/lib/i18n/server";
import { loadMeta } from "@/lib/meta";

export async function generateMetadata(): Promise<Metadata> {
  const { t } = await getStrings();
  const meta = await loadMeta();
  return {
    title: t.pages.rwa.metaTitle,
    description: t.pages.rwa.metaDescription(meta.email_alerts),
  };
}

/** How a residents' group watches a project with Neev Sentinel. */
export default async function RwaPage() {
  const { t } = await getStrings();
  const meta = await loadMeta();
  const copy = t.pages.rwa;

  return (
    <>
      <PageHead title={copy.title} lead={copy.lead} />

      <section className={styles.section} aria-labelledby="watch-title">
        <h2 id="watch-title" className={styles.heading}>
          {copy.stepsTitle}
        </h2>
        <Steps steps={copy.steps(meta.email_alerts)} />
        <p className={styles.text}>{copy.budgetNote}</p>
      </section>

      <RwaSignIn />
    </>
  );
}
