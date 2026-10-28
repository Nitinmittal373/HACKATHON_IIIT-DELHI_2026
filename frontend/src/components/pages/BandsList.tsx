import type { Strings } from "@/lib/i18n";
import { BAND_TONE } from "@/lib/neevScore";
import type { Meta } from "@/lib/types";
import styles from "./pages.module.css";

/** The bands from /api/meta, highest first, each with its range. Colour never stands alone. */
export function BandsList({ meta, t }: { meta: Meta; t: Strings }) {
  return (
    <ul className={`${styles.list} ${styles.plain}`}>
      {meta.bands.map((band) => (
        <li key={band.key} className={styles.band} data-tone={BAND_TONE[band.key]}>
          {t.pages.how.bandLine(t.score.bands[band.key], band.min, band.max)}
        </li>
      ))}
    </ul>
  );
}
