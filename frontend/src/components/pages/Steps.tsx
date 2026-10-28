import styles from "./pages.module.css";

/** A numbered list of short steps, each with a title and one sentence. */
export function Steps({ steps }: { steps: { title: string; body: string }[] }) {
  return (
    <ol className={styles.steps}>
      {steps.map((step, index) => (
        <li key={step.title}>
          <span className={styles.stepNumber}>{index + 1}</span>
          <span className={styles.stepTitle}>{step.title}</span>
          <span className={styles.stepBody}>{step.body}</span>
        </li>
      ))}
    </ol>
  );
}
