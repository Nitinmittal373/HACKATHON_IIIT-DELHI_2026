"use client";

import { useState } from "react";

import { EvidenceLedger } from "@/components/report/EvidenceLedger";
import { useLang } from "@/lib/LangProvider";
import { reasonLabel, type LedgerRow } from "@/lib/scoreV2";
import type { ReasonCode } from "@/lib/types";
import styles from "./ReasonChips.module.css";

interface Props {
  reasons: ReasonCode[];
  rows: LedgerRow[];
  rera: string;
}

/** The top reason codes as chips; each opens the evidence ledger on its own records. */
export function ReasonChips({ reasons, rows, rera }: Props) {
  const { t, lang } = useLang();
  const [open, setOpen] = useState(false);
  const [code, setCode] = useState<string | null>(null);

  function show(next: string | null) {
    setCode(next);
    setOpen(true);
  }

  return (
    <section aria-labelledby="reasons-title">
      <h3 id="reasons-title" className={styles.title}>
        {t.credit.reasonsTitle}
      </h3>
      {reasons.length === 0 ? (
        <p className={styles.none}>{t.credit.noReasons}</p>
      ) : (
        <ul className={`${styles.chips} noPrint`}>
          {reasons.map((reason) => (
            <li key={reason.code}>
              <button
                type="button"
                className={styles.chip}
                data-unread={reason.code === "R12"}
                aria-label={`${reason.code}: ${reasonLabel(reason, t.credit.codes, lang)}. ${t.credit.reasonOpen(reason.code)}`}
                aria-haspopup="dialog"
                onClick={() => show(reason.code)}
              >
                <span className={`mono ${styles.code}`}>{reason.code}</span>
                <span className={styles.label}>{reasonLabel(reason, t.credit.codes, lang)}</span>
                <span className={`num ${styles.points}`}>
                  {reason.points ? `−${Math.abs(Math.round(reason.points))}` : t.credit.unread}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
      {reasons.some((reason) => reason.code === "R12") && <p className={styles.note}>{t.credit.r12Note}</p>}
      <button type="button" className={`btn2 ${styles.open} noPrint`} aria-haspopup="dialog" onClick={() => show(null)}>
        {t.credit.ledger.open}
      </button>
      <EvidenceLedger
        rows={rows}
        rera={rera}
        open={open}
        code={code}
        codes={reasons.filter((reason) => reason.finding_ids.length).map((reason) => reason.code)}
        onFilter={setCode}
        onClose={() => setOpen(false)}
      />
    </section>
  );
}
