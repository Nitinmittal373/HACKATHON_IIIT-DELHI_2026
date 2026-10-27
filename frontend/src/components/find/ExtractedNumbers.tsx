"use client";

import { useRouter } from "next/navigation";

import { useLang } from "@/lib/LangProvider";
import type { ExtractResponse } from "@/lib/types";
import styles from "./MoreWays.module.css";

/** The numbers found in a file or QR code, each with the words around it, ready to search. */
export function ExtractedNumbers({ result }: { result: ExtractResponse }) {
  const router = useRouter();
  const { t } = useLang();
  const copy = t.find.more.results;

  if (result.numbers.length === 0) {
    return (
      <p className={styles.status} role="status">
        {result.message ?? copy.none}
      </p>
    );
  }

  return (
    <div className={styles.found} role="status">
      <h3 className="eyebrow">{result.source === "your QR code" ? copy.titleQr : copy.titleDocument}</h3>
      {result.numbers.map((found) => {
        const candidate = result.candidates.find((c) => c.rera_id === found.rera_id);
        return (
          <div key={found.rera_id} className={styles.hit}>
            <span>
              <b className="mono">{found.rera_id}</b>
              <span className={styles.line}>“{found.line}”</span>
              <span className={styles.line}>
                {candidate?.status === "confirmed" ? copy.confirmed : copy.unconfirmed}
              </span>
            </span>
            <button
              type="button"
              className="btn"
              onClick={() => router.push(`/check?q=${encodeURIComponent(found.rera_id)}`)}
            >
              {copy.use}
            </button>
          </div>
        );
      })}
    </div>
  );
}
