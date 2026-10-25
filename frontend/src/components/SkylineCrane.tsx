import { GROUND_Y, type Crane } from "@/lib/skyline";
import styles from "./Skyline.module.css";

const STROKE = "#F26B1D";

/** A tower crane: lattice mast, a jib that slews (scaleX), a bobbing hook and a red beacon. */
export function SkylineCrane({ crane, delay }: { crane: Crane; delay: number }) {
  const { x, top, reach } = crane;
  const hookX = x + Math.round(reach * 0.7);
  const latticeRows = Math.floor((GROUND_Y - top - 10) / 14) + 1;
  const lattice = Array.from({ length: latticeRows }, (_, i) => top + 10 + i * 14);

  return (
    <g>
      <line x1={x} x2={x} y1={GROUND_Y} y2={top} stroke={STROKE} strokeWidth={2} strokeOpacity={0.7} />
      {lattice.map((y) => (
        <line key={y} x1={x - 4} x2={x + 4} y1={y} y2={y + 10} stroke={STROKE} strokeOpacity={0.35} />
      ))}
      <g
        className={styles.jib}
        style={{ transformOrigin: `${x}px ${top}px`, animationDelay: `${delay}s` }}
      >
        <line
          x1={x - 40}
          x2={x + reach}
          y1={top}
          y2={top}
          stroke={STROKE}
          strokeWidth={2.4}
          strokeOpacity={0.8}
        />
        <line x1={x} x2={x + reach} y1={top - 16} y2={top} stroke={STROKE} strokeOpacity={0.45} />
        <line x1={x} x2={x - 40} y1={top - 16} y2={top} stroke={STROKE} strokeOpacity={0.45} />
        <rect x={x - 46} y={top - 2} width={12} height={10} fill={STROKE} fillOpacity={0.5} />
        <g className={styles.hook}>
          <line x1={hookX} x2={hookX} y1={top} y2={top + 46} stroke="#111" strokeOpacity={0.5} />
          <rect x={hookX - 9} y={top + 46} width={18} height={9} fill={STROKE} fillOpacity={0.7} />
        </g>
      </g>
      <line x1={x} x2={x} y1={top} y2={top - 18} stroke={STROKE} strokeWidth={2} strokeOpacity={0.7} />
      <circle className={styles.beacon} cx={x} cy={top - 20} r={3} fill="#E5484D" />
    </g>
  );
}
