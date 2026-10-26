"use client";

import { ExternalLinkIcon } from "@/components/report/ExternalLinkIcon";
import type { FamilyNode } from "@/lib/family";
import { useLang } from "@/lib/LangProvider";
import styles from "./FamilyTree.module.css";

/** What the records say about the chosen node, announced politely when it changes. */
export function FamilyNodeDetails({ node }: { node: FamilyNode | null }) {
  const { t } = useLang();

  return (
    <aside className={styles.details} aria-live="polite" aria-labelledby="family-details-title">
      <h3 id="family-details-title" className={styles.detailsTitle}>
        {t.family.detailsTitle}
      </h3>
      {node === null ? (
        <p className={styles.hint}>{t.family.detailsHint}</p>
      ) : (
        <>
          <p className={styles.kind}>{t.family.kinds[node.kind]}</p>
          <p className={styles.detailName}>{node.label}</p>
          {node.kind === "director" && node.sub && <p>{node.sub}</p>}
          {node.kind === "company" && (
            <p>{node.sub ? t.family.status(node.sub) : t.family.statusUnknown}</p>
          )}
          {node.kind === "project" && node.sub && <p className="mono">{node.sub}</p>}
          {node.flag && <p className={styles.flagLine}>{t.family.flags[node.flag]}</p>}
          {node.kind === "company" && <p className={styles.hint}>{t.family.linkNote}</p>}
          {node.href && (
            <a className={styles.source} href={node.href} target="_blank" rel="noopener noreferrer">
              {t.family.sourcePage}
              <ExternalLinkIcon />
              <span className="sr"> ({t.common.opensInNewTab})</span>
            </a>
          )}
        </>
      )}
    </aside>
  );
}
