import Link from "next/link";

import type { Strings } from "@/lib/i18n";
import type { OrderLead } from "@/lib/types";
import styles from "./ResultCards.module.css";

/** A public order that names the project's builder, when nothing else found the project. */
export function OrderLeadCard({ lead, t }: { lead: OrderLead; t: Strings }) {
  const copy = t.find.orderLead;
  return (
    <section className={`card ${styles.card} ${styles.soft}`} aria-label={copy.title}>
      <h2 className={styles.title}>{copy.title}</h2>
      <p className={styles.body}>{copy.body(lead.builder)}</p>
      <p className={styles.body}>
        <a className={styles.link} href={lead.order_url} target="_blank" rel="noopener noreferrer">
          {copy.link}: {lead.order_title}
        </a>
      </p>
      <div className={styles.actions}>
        <Link href={`/check?builder=${encodeURIComponent(lead.builder)}`} className="btn2">
          {copy.button}
        </Link>
      </div>
    </section>
  );
}
