import styles from "./Glow.module.css";

/** Two drifting orange lights and, optionally, a faint dot grid. Purely decorative. */
export function Glow({ dots = false, soft = false }: { dots?: boolean; soft?: boolean }) {
  return (
    <>
      <div className={`${styles.blob} ${styles.one} ${soft ? styles.soft : ""}`} aria-hidden="true" />
      <div className={`${styles.blob} ${styles.two} ${soft ? styles.soft : ""}`} aria-hidden="true" />
      {dots && <div className={styles.dots} aria-hidden="true" />}
    </>
  );
}
