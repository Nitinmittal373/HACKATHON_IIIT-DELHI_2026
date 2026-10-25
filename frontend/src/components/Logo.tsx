import styles from "./Logo.module.css";

/** The house-and-check mark with the NeevCheck name. */
export function Logo() {
  return (
    <span className={styles.logo}>
      <svg width="30" height="30" viewBox="0 0 32 32" aria-hidden="true">
        <rect width="32" height="32" rx="8" fill="#F26B1D" />
        <path d="M8 15.5 16 9l8 6.5" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M12 17.5l3 3 5.5-5.5" fill="none" stroke="#FFE1CC" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" />
        <path d="M8 24h16" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" />
      </svg>
      <span className={styles.name}>NeevCheck</span>
    </span>
  );
}
