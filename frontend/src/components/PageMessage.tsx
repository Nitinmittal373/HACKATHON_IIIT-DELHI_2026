import type { ReactNode } from "react";

import styles from "./PageMessage.module.css";

interface Props {
  title: string;
  children?: ReactNode;
  /** Buttons or links shown under the text. */
  actions?: ReactNode;
  /** Announce the message to screen readers, for errors that appear after an action. */
  alert?: boolean;
}

/** A calm, specific message for empty and error states. */
export function PageMessage({ title, children, actions, alert = false }: Props) {
  return (
    <section className={`card ${styles.box}`} role={alert ? "alert" : undefined}>
      <h2 className={styles.title}>{title}</h2>
      {children && <div className={styles.body}>{children}</div>}
      {actions && <div className={styles.actions}>{actions}</div>}
    </section>
  );
}
