import { SkylineCrane } from "@/components/SkylineCrane";
import { SkylineTower } from "@/components/SkylineTower";
import {
  GROUND_Y,
  SKY_HEIGHT,
  SKY_WIDTH,
  TOWERS,
  farBlocks,
  seededRandom,
  windowsFor,
} from "@/lib/skyline";
import styles from "./Skyline.module.css";

const STROKE = "#F26B1D";
const HATCH_STEP = 24;

interface Props {
  /** "hero" sits at the bottom of the hero; "app" is a fixed, softer scene behind a whole page. */
  variant: "hero" | "app";
}

/** The animated construction skyline: towers rising, cranes working, a running "neev" line. */
export function Skyline({ variant }: Props) {
  const random = seededRandom(7);
  const far = farBlocks(random);
  const windows = TOWERS.map((tower) => windowsFor(tower, random));
  const hatch = Array.from({ length: SKY_WIDTH / HATCH_STEP }, (_, i) => i * HATCH_STEP);

  const svg = (
    <svg
      className={variant === "hero" ? styles.hero : styles.app}
      viewBox={`0 0 ${SKY_WIDTH} ${SKY_HEIGHT}`}
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="skylineFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#FFFFFF" />
          <stop offset="1" stopColor="#FFF3EA" />
        </linearGradient>
      </defs>
      <g className={styles.far} fill="#FBE3D2" opacity={0.55}>
        {far.map((block) => (
          <rect
            key={block.x}
            x={block.x}
            y={block.y}
            width={block.width}
            height={block.height}
            rx={2}
          />
        ))}
      </g>
      {TOWERS.map((tower, index) => (
        <g key={tower.x}>
          <SkylineTower tower={tower} windows={windows[index] ?? []} delay={0.25 + index * 0.18} />
          {tower.crane && <SkylineCrane crane={tower.crane} delay={index < 4 ? 2.6 : 6.5} />}
        </g>
      ))}
      <line
        x1={0}
        x2={SKY_WIDTH}
        y1={GROUND_Y}
        y2={GROUND_Y}
        stroke={STROKE}
        strokeOpacity={0.5}
        strokeWidth={1.5}
      />
      <line
        className={styles.neevGlow}
        x1={0}
        x2={SKY_WIDTH}
        y1={GROUND_Y}
        y2={GROUND_Y}
        stroke={STROKE}
        strokeOpacity={0.25}
        strokeWidth={10}
        strokeLinecap="round"
      />
      <line
        className={styles.neevRun}
        x1={0}
        x2={SKY_WIDTH}
        y1={GROUND_Y}
        y2={GROUND_Y}
        stroke={STROKE}
        strokeWidth={3}
        strokeLinecap="round"
      />
      {hatch.map((x) => (
        <line
          key={x}
          x1={x}
          x2={x - 8}
          y1={GROUND_Y}
          y2={GROUND_Y + 12}
          stroke={STROKE}
          strokeOpacity={0.25}
        />
      ))}
    </svg>
  );

  if (variant === "hero") return svg;
  return <div className={styles.scene}>{svg}</div>;
}
