import styles from "./pages.module.css";

/** The title and one line under it, left-aligned like every inner page. */
export function PageHead({ title, lead }: { title: string; lead: string }) {
  return (
    <header className={styles.page}>
      <h1 className={`h2 ${styles.title}`}>{title}</h1>
      <p className={styles.lead}>{lead}</p>
    </header>
  );
}
