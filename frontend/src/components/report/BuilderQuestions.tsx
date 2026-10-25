import { CopyQuestions } from "@/components/report/CopyQuestions";
import { builderQuestions } from "@/lib/builderQuestions";
import type { Strings } from "@/lib/i18n";
import type { Report } from "@/lib/types";
import styles from "./BuilderQuestions.module.css";

/** Five questions chosen from the findings, ready to copy into a message to the builder. */
export function BuilderQuestions({ report, t }: { report: Report; t: Strings }) {
  const questions = builderQuestions(report).map((key) => t.insights.questions.items[key]);
  return (
    <section className={`card ${styles.card}`} aria-labelledby="questions-title">
      <h2 id="questions-title" className={styles.title}>
        {t.insights.questions.title}
      </h2>
      <p className={styles.lead}>{t.insights.questions.lead}</p>
      <ol className={styles.list}>
        {questions.map((question) => (
          <li key={question}>{question}</li>
        ))}
      </ol>
      <CopyQuestions text={questions.map((question, index) => `${index + 1}. ${question}`).join("\n")} />
    </section>
  );
}
