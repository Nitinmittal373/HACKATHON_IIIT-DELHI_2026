import {
  FLOOR_HEIGHT,
  GROUND_Y,
  columnCount,
  towerTop,
  type Tower,
  type Window,
} from "@/lib/skyline";
import styles from "./Skyline.module.css";

interface Props {
  tower: Tower;
  windows: Window[];
  /** Seconds before the tower starts rising. */
  delay: number;
}

const STROKE = "#F26B1D";

/** One tower: it rises floor by floor, then its windows light up one by one. */
export function SkylineTower({ tower, windows, delay }: Props) {
  const top = towerTop(tower);
  const columns = columnCount(tower);
  const { x, width, floors } = tower;

  return (
    <>
      <g
        className={styles.tower}
        style={{ animationDelay: `${delay}s`, animationTimingFunction: `steps(${floors}, end)` }}
      >
        <rect
          x={x}
          y={top}
          width={width}
          height={GROUND_Y - top}
          fill="url(#skylineFill)"
          stroke={STROKE}
          strokeOpacity={0.45}
          strokeWidth={1.2}
        />
        {Array.from({ length: floors - 1 }, (_, i) => {
          const y = GROUND_Y - FLOOR_HEIGHT * (i + 1);
          return (
            <line key={y} x1={x} x2={x + width} y1={y} y2={y} stroke={STROKE} strokeOpacity={0.14} />
          );
        })}
        {Array.from({ length: columns - 1 }, (_, i) => {
          const lineX = x + ((i + 1) * width) / columns;
          return (
            <line
              key={lineX}
              x1={lineX}
              x2={lineX}
              y1={top}
              y2={GROUND_Y}
              stroke={STROKE}
              strokeOpacity={0.08}
            />
          );
        })}
        {windows.map((w) => (
          <rect
            key={`${w.x}-${w.y}`}
            className={styles.window}
            x={w.x}
            y={w.y}
            width={w.width}
            height={6}
            fill={STROKE}
            style={{ animationDelay: `${w.delay}s`, animationDuration: `${w.duration}s` }}
          />
        ))}
      </g>
      {tower.building &&
        [1, 2, 3, 4].map((slab) => (
          <rect
            key={slab}
            className={styles.slab}
            x={x}
            y={top - FLOOR_HEIGHT * slab}
            width={width}
            height={FLOOR_HEIGHT}
            fill="none"
            stroke={STROKE}
            strokeOpacity={0.6}
            strokeDasharray="4 4"
            style={{ animationDelay: `${0.9 * slab}s` }}
          />
        ))}
    </>
  );
}
