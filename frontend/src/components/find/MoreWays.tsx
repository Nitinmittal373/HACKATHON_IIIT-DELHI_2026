"use client";

import { useId, useRef, useState, type KeyboardEvent } from "react";

import { BuilderForm } from "@/components/find/BuilderForm";
import { DocumentUpload } from "@/components/find/DocumentUpload";
import { LocalityForm } from "@/components/find/LocalityForm";
import { QrScan } from "@/components/find/QrScan";
import { useLang } from "@/lib/LangProvider";
import styles from "./MoreWays.module.css";

const TABS = ["builder", "locality", "document", "qr"] as const;
type Tab = (typeof TABS)[number];

/** For projects with no website: find them by builder, by place, from a brochure or a QR code. */
export function MoreWays() {
  const { t } = useLang();
  const base = useId();
  const [tab, setTab] = useState<Tab>("builder");
  const buttons = useRef<Record<Tab, HTMLButtonElement | null>>({
    builder: null,
    locality: null,
    document: null,
    qr: null,
  });

  // Arrow keys move between the tabs, as a tab list does everywhere else.
  function move(event: KeyboardEvent<HTMLDivElement>) {
    const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (step === 0) return;
    event.preventDefault();
    const next = TABS.at((TABS.indexOf(tab) + step) % TABS.length) ?? tab;
    setTab(next);
    buttons.current[next]?.focus();
  }

  return (
    <details id="more" className={styles.more}>
      <summary className={styles.summary}>
        {t.find.more.summary}
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" aria-hidden="true">
          <path d="m6 9 6 6 6-6" />
        </svg>
      </summary>
      <div className={`card ${styles.panel}`}>
        <p className={styles.lead}>{t.find.more.lead}</p>
        <div className={styles.tabs} role="tablist" aria-label={t.find.more.tabsLabel} onKeyDown={move}>
          {TABS.map((id) => (
            <button
              key={id}
              ref={(node) => {
                buttons.current[id] = node;
              }}
              type="button"
              role="tab"
              id={`${base}-tab-${id}`}
              aria-selected={tab === id}
              aria-controls={`${base}-panel`}
              tabIndex={tab === id ? 0 : -1}
              className={styles.tab}
              onClick={() => setTab(id)}
            >
              {t.find.more.tabs[id]}
            </button>
          ))}
        </div>
        <div role="tabpanel" id={`${base}-panel`} aria-labelledby={`${base}-tab-${tab}`}>
          {tab === "builder" && <BuilderForm />}
          {tab === "locality" && <LocalityForm />}
          {tab === "document" && <DocumentUpload />}
          {tab === "qr" && <QrScan />}
        </div>
      </div>
    </details>
  );
}
