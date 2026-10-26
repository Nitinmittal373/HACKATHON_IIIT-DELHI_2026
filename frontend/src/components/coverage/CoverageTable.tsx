import { StateBadge } from "@/components/StateBadge";
import { ExternalLinkIcon } from "@/components/report/ExternalLinkIcon";
import type { Lang, Strings } from "@/lib/i18n";
import { stateLabel } from "@/lib/states";
import type { StateInfo } from "@/lib/types";
import styles from "./CoverageTable.module.css";

interface Props {
  states: StateInfo[];
  t: Strings;
  lang: Lang;
}

/** A map-free table of every state: its authority, how deeply it is read, and real examples. */
export function CoverageTable({ states, t, lang }: Props) {
  const c = t.states.coverage;
  return (
    <div className={`card ${styles.wrap}`}>
      <table className={styles.table}>
        <thead>
          <tr>
            <th scope="col">{c.columns.state}</th>
            <th scope="col">{c.columns.authority}</th>
            <th scope="col">{c.columns.level}</th>
            <th scope="col">{c.columns.read}</th>
            <th scope="col">{c.columns.examples}</th>
            <th scope="col">{c.columns.portal}</th>
          </tr>
        </thead>
        <tbody>
          {states.map((state) => (
            <tr key={state.code}>
              <th scope="row">
                <StateBadge code={state.code} name={state.name} rera={state.rera_name} t={t} lang={lang} />{" "}
                {stateLabel(state.code, state.name, lang)}
              </th>
              <td>{state.rera_name}</td>
              <td>
                <span className={`${styles.level} ${styles[state.coverage]}`}>
                  {t.states.levels[state.coverage]}
                </span>
              </td>
              <td className={styles.read}>{state.note}</td>
              <td>
                {state.examples.length > 0 ? (
                  <ul className={`mono ${styles.examples}`}>
                    {state.examples.map((example) => (
                      <li key={example}>{example}</li>
                    ))}
                  </ul>
                ) : (
                  <span className={styles.muted}>{c.noExamples}</span>
                )}
                {!state.format_verified && <p className={styles.muted}>{c.formatNotVerified}</p>}
              </td>
              <td>
                <a href={state.portal_url} target="_blank" rel="noopener noreferrer" className={styles.link}>
                  {c.open}
                  <ExternalLinkIcon />
                  <span className="sr"> ({t.common.opensInNewTab})</span>
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
