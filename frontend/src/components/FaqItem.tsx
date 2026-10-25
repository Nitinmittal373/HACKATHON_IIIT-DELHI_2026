import styles from "./Faq.module.css";

interface Props {
  id: string;
  question: string;
  answer: string;
  open: boolean;
  onToggle: () => void;
}

/** One question: a real button controls the answer panel. */
export function FaqItem({ id, question, answer, open, onToggle }: Props) {
  return (
    <div className={styles.item}>
      <h3 className={styles.heading}>
        <button
          type="button"
          className={styles.question}
          aria-expanded={open}
          aria-controls={`${id}-panel`}
          id={`${id}-button`}
          onClick={onToggle}
        >
          <span>{question}</span>
          <span className={`${styles.icon} ${open ? styles.iconOpen : ""}`} aria-hidden="true">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <path d="M12 5v14M5 12h14" />
            </svg>
          </span>
        </button>
      </h3>
      <div
        className={`${styles.panel} ${open ? styles.panelOpen : ""}`}
        id={`${id}-panel`}
        role="region"
        aria-labelledby={`${id}-button`}
      >
        <div className={styles.clip}>
          <p>{answer}</p>
        </div>
      </div>
    </div>
  );
}
