import type { CSSProperties } from "react";

import styles from "./Skeleton.module.css";

interface Props {
  width?: number | string;
  height?: number | string;
  style?: CSSProperties;
}

/** A pale pulsing block that holds a place while a page loads. */
export function Skeleton({ width = "100%", height = 16, style }: Props) {
  return <div className={styles.block} style={{ width, height, ...style }} aria-hidden="true" />;
}
