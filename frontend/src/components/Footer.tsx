import styles from "./Footer.module.css";

export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={`wrap ${styles.row}`}>
        <span>NeevCheck · Team RYZEN, KIET · HackIIITD 2026</span>
        <span>Built on public records, read by TinyFish agents</span>
      </div>
    </footer>
  );
}
