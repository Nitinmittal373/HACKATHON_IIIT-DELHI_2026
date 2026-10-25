import Link from "next/link";

import type { ExampleReport } from "@/lib/exampleReport";
import styles from "./AgentDemo.module.css";

const STEPS = [
  "Finds your project on UP-RERA",
  "Reads the registration date",
  "Reads the promised completion date",
  "Counts every extension",
];

/** The looping mini browser. It repeats a 12 second loop, one step every three seconds. */
export function AgentDemo({ report }: { report: ExampleReport }) {
  const { register } = report;
  const rows: [string, string][] = [
    ["Project name", report.name.toUpperCase()],
    ["Promoter", report.promoter],
    ["Registration date", register.registeredOn],
    ["Proposed completion", register.completionDue],
    ["Extensions", register.extensions],
  ];
  const found = [
    { text: "Project matched", tone: "ok" },
    { text: register.registeredLabel, tone: "ok" },
    { text: register.dueLabel, tone: "warn" },
    { text: register.extensionsLabel, tone: "ok" },
  ];

  return (
    <section className="wrap section" id="how-it-works" aria-labelledby="demo-title">
      <div className={styles.demo}>
        <div className="rv">
          <div className="eyebrow">Powered by TinyFish</div>
          <h2 id="demo-title" className={`h2 ${styles.title}`}>
            Watch an agent read the records for you
          </h2>
          <p className={styles.lead}>
            A TinyFish browser agent opens each official site, finds your project and copies the
            exact record, with the link and the minute it read it.
          </p>
          <ol className={styles.steps}>
            {STEPS.map((step, index) => (
              <li key={step} style={{ ["--i" as string]: index }}>
                <span className="mono">{String(index + 1).padStart(2, "0")}</span>
                {step}
              </li>
            ))}
          </ol>
          <Link href="/#search" className={`btn ${styles.cta}`}>
            Try it on a project
            <svg className="arrow" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </Link>
        </div>

        <figure className={`${styles.figure} rv`}>
          <div
            className={styles.window}
            role="img"
            aria-label={`Illustration of an agent reading the UP-RERA page of ${report.name}`}
          >
            <div className={styles.bar} aria-hidden="true">
              <span />
              <span />
              <span />
              <em className="mono">up-rera.in · {report.reraId}</em>
              <b className="mono">
                <i className={styles.rec} />
                EXAMPLE
              </b>
            </div>
            <div className={styles.page} aria-hidden="true">
              <div className={styles.head}>Project details</div>
              {rows.map(([label, value]) => (
                <div key={label} className={styles.row}>
                  <span>{label}</span>
                  <b>{value}</b>
                </div>
              ))}
              <div className={styles.highlight} />
              <svg className={styles.cursor} viewBox="0 0 24 24">
                <path d="M4 2l16 9-7 2-3 7z" fill="#111" stroke="#fff" strokeWidth="1.5" strokeLinejoin="round" />
              </svg>
            </div>
            <div className={styles.found} aria-hidden="true">
              {found.map((chip, index) => (
                <div key={chip.text} className={styles.chip} style={{ animationDelay: `${1.2 + index * 3}s` }}>
                  <span className={`${styles.dot} ${styles[chip.tone]}`} />
                  {chip.text}
                </div>
              ))}
            </div>
          </div>
          <figcaption className={styles.caption}>
            Illustration of a live check. The values are from the check of {report.reraId} read on{" "}
            {report.readOn}.
          </figcaption>
        </figure>
      </div>
    </section>
  );
}
