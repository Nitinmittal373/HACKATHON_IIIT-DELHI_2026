import { getStrings } from "@/lib/i18n/server";
import styles from "./Footer.module.css";

export async function Footer() {
  const { t } = await getStrings();
  return (
    <footer className={styles.footer}>
      <div className={`wrap ${styles.row}`}>
        <span>{t.home.footer.left}</span>
        <span>{t.home.footer.right}</span>
      </div>
    </footer>
  );
}
