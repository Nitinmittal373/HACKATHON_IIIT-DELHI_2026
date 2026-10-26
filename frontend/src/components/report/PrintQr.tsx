"use client";

import qrcode from "qrcode-generator";
import { useEffect, useState } from "react";

import { useLang } from "@/lib/LangProvider";
import styles from "./PrintQr.module.css";

/** A QR code to the live report. It is only visible on the printed page. */
export function PrintQr() {
  const { t } = useLang();
  const [svg, setSvg] = useState<string | null>(null);

  useEffect(() => {
    const code = qrcode(0, "M");
    code.addData(window.location.href);
    code.make();
    setSvg(code.createSvgTag({ cellSize: 3, margin: 0, scalable: true }));
  }, []);

  if (!svg) return null;
  return (
    <figure className={styles.qr}>
      <div role="img" aria-label={t.legal.qr.label} dangerouslySetInnerHTML={{ __html: svg }} />
      <figcaption>{t.legal.qr.caption}</figcaption>
    </figure>
  );
}
