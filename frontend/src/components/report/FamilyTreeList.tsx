"use client";

import type { FamilyNode } from "@/lib/family";
import { useLang } from "@/lib/LangProvider";
import styles from "./FamilyTree.module.css";

interface Props {
  nodes: FamilyNode[];
  selected: string | null;
  onSelect: (id: string) => void;
}

const TIERS = [
  { tier: 0, key: "promoter" },
  { tier: 1, key: "directors" },
  { tier: 2, key: "companies" },
  { tier: 3, key: "projects" },
] as const;

/** The same tree as a plain list: for phones and for anyone not using the diagram. */
export function FamilyTreeList({ nodes, selected, onSelect }: Props) {
  const { t } = useLang();

  return (
    <div className={styles.list}>
      <h3 className={styles.listTitle}>{t.family.listTitle}</h3>
      {TIERS.map(({ tier, key }) => {
        const members = nodes.filter((node) => node.tier === tier);
        return (
          <section key={key} aria-label={t.family.tiers[key]}>
            <h4 className={styles.tierTitle}>{t.family.tiers[key]}</h4>
            {members.length === 0 ? (
              <p className={styles.none}>{t.family.none}</p>
            ) : (
              <ul className={styles.items}>
                {members.map((node) => {
                  const flag = node.flag ? t.family.flags[node.flag] : null;
                  return (
                    <li key={node.id}>
                      <button
                        type="button"
                        className={styles.item}
                        data-flag={node.flag ?? "none"}
                        aria-pressed={selected === node.id}
                        onClick={() => onSelect(node.id)}
                      >
                        <span className={styles.itemName}>{node.label}</span>
                        <span className={styles.itemSub}>
                          {flag ?? node.sub ?? (node.kind === "company" ? t.family.statusUnknown : "")}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        );
      })}
    </div>
  );
}
