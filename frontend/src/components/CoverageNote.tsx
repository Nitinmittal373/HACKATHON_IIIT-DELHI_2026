import { ExternalLinkIcon } from "@/components/report/ExternalLinkIcon";
import type { Strings } from "@/lib/i18n";
import type { Coverage } from "@/lib/states";
import styles from "./CoverageNote.module.css";

interface Props {
  coverage: Coverage;
  rera: string;
  /** The portal's own page, opened for the full record. */
  href: string;
  t: Strings;
}

/** One sentence saying how the facts were read, with the portal link where they were not opened. */
export function CoverageNote({ coverage, rera, href, t }: Props) {
  if (coverage === "full") return <p className={styles.note}>{t.states.reading.full}</p>;
  if (coverage === "partial") return <p className={styles.note}>{t.states.reading.partial}</p>;
  return (
    <p className={styles.note}>
      {t.states.reading.searchOnly(rera)}{" "}
      <a href={href} target="_blank" rel="noopener noreferrer" className={styles.link}>
        {t.states.openOn(rera)}
        <ExternalLinkIcon />
        <span className="sr"> ({t.common.opensInNewTab})</span>
      </a>
    </p>
  );
}
