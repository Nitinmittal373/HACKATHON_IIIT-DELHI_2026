"use client";

import { useMemo, useState } from "react";

import { FamilyNodeDetails } from "@/components/report/FamilyNodeDetails";
import { FamilyTreeGraph } from "@/components/report/FamilyTreeGraph";
import { FamilyTreeList } from "@/components/report/FamilyTreeList";
import { familyNodes, layoutFamily } from "@/lib/family";
import { useLang } from "@/lib/LangProvider";
import type { FamilyTree as Tree } from "@/lib/types";
import styles from "./FamilyTree.module.css";

/** The builder's group: promoter, directors, related companies and their projects. */
export function FamilyTree({ tree }: { tree: Tree }) {
  const { t } = useLang();
  const nodes = useMemo(() => familyNodes(tree), [tree]);
  const layout = useMemo(() => layoutFamily(nodes), [nodes]);
  const [selected, setSelected] = useState<string | null>(null);
  const chosen = nodes.find((node) => node.id === selected) ?? null;

  return (
    <section className={`card ${styles.card}`} aria-labelledby="family-title">
      <h2 id="family-title" className={styles.title}>
        {t.family.title}
      </h2>
      <p className={styles.lead}>{t.family.lead}</p>
      <p className={styles.legend}>{t.family.legend}</p>
      <div className={styles.body}>
        <div className={styles.graph}>
          <FamilyTreeGraph layout={layout} selected={selected} onSelect={setSelected} />
        </div>
        <FamilyNodeDetails node={chosen} />
      </div>
      <FamilyTreeList nodes={nodes} selected={selected} onSelect={setSelected} />
    </section>
  );
}
