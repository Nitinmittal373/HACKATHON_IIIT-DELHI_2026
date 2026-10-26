"use client";

import { useEffect, useRef } from "react";

import { ExternalLinkIcon } from "@/components/report/ExternalLinkIcon";
import { formatDay, formatTime } from "@/lib/format";
import { relabel } from "@/lib/i18n/relabel";
import { useLang } from "@/lib/LangProvider";
import type { LedgerRow } from "@/lib/scoreV2";
import styles from "./EvidenceLedger.module.css";

interface Props {
  rows: LedgerRow[];
  open: boolean;
  /** The reason code the ledger is narrowed to, or null for every record. */
  code: string | null;
  codes: string[];
  /** The state's authority, so the source reads MahaRERA, not UP-RERA. */
  rera: string;
  onFilter: (code: string | null) => void;
  onClose: () => void;
}

/** A side drawer listing every claim with its page, read time, excerpt, points and reason code. */
export function EvidenceLedger({ rows, open, code, codes, rera, onFilter, onClose }: Props) {
  const { t: base, lang } = useLang();
  const t = relabel(base, rera);
  const dialog = useRef<HTMLDialogElement>(null);
  const shown = code ? rows.filter((row) => row.code === code) : rows;

  useEffect(() => {
    const element = dialog.current;
    if (!element) return;
    if (open && !element.open) element.showModal();
    if (!open && element.open) element.close();
  }, [open]);

  return (
    <dialog
      ref={dialog}
      className={styles.drawer}
      aria-labelledby="ledger-title"
      onClose={onClose}
      onClick={(event) => event.target === dialog.current && onClose()}
    >
      <div className={styles.panel}>
        <header className={styles.head}>
          <div>
            <h2 id="ledger-title" className={styles.title}>
              {t.credit.ledger.title}
            </h2>
            <p className={styles.lead}>{t.credit.ledger.lead}</p>
          </div>
          <button type="button" className="btn2" onClick={onClose}>
            {t.credit.ledger.close}
          </button>
        </header>

        <div className={styles.filters} role="group" aria-label={t.credit.ledger.filterLabel}>
          <button type="button" className={styles.filter} aria-pressed={code === null} onClick={() => onFilter(null)}>
            {t.credit.ledger.all}
          </button>
          {codes.map((entry) => (
            <button
              key={entry}
              type="button"
              className={`mono ${styles.filter}`}
              aria-pressed={code === entry}
              onClick={() => onFilter(entry)}
            >
              {entry}
            </button>
          ))}
        </div>

        {shown.length === 0 ? (
          <p className={styles.empty}>{t.credit.ledger.empty}</p>
        ) : (
          <ol className={styles.list}>
            {shown.map((row) => (
              <li key={row.evidenceId} className={styles.item} id={`ledger-${row.evidenceId}`}>
                <div className={styles.itemHead}>
                  <span className={`mono ${styles.id}`}>{row.evidenceId}</span>
                  <span className={styles.name}>{row.title}</span>
                </div>
                <dl className={styles.facts}>
                  <div>
                    <dt>{t.credit.ledger.source}</dt>
                    <dd>
                      {t.cam.sourceLabels[row.source]} · {t.report.reliability[row.reliability]}
                      {row.via && ` (${t.report.viaSnippet})`}
                    </dd>
                  </div>
                  <div>
                    <dt>{t.credit.ledger.read}</dt>
                    <dd>{t.report.readOn(formatDay(row.readOn, lang), row.readAt ? formatTime(row.readAt, lang) : null)}</dd>
                  </div>
                  <div>
                    <dt>{t.credit.ledger.points}</dt>
                    <dd>{row.points ? `−${Math.abs(Math.round(row.points * 10) / 10)}` : t.credit.ledger.noPoints}</dd>
                  </div>
                  <div>
                    <dt>{t.credit.ledger.code}</dt>
                    <dd className="mono">{row.code ?? t.credit.ledger.noCode}</dd>
                  </div>
                </dl>
                <blockquote className={styles.snippet}>{row.snippet ?? t.credit.ledger.noSnippet}</blockquote>
                <a className={styles.page} href={row.sourceUrl} target="_blank" rel="noopener noreferrer">
                  {t.credit.ledger.openPage}
                  <ExternalLinkIcon />
                  <span className="sr"> ({t.common.opensInNewTab})</span>
                </a>
              </li>
            ))}
          </ol>
        )}
      </div>
    </dialog>
  );
}
