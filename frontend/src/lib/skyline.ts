/** The skyline is drawn from this small description. Positions are seeded so every render matches. */

export const SKY_WIDTH = 1440;
export const SKY_HEIGHT = 440;
export const GROUND_Y = 420;
export const FLOOR_HEIGHT = 12;

export interface Crane {
  /** x of the mast. */
  x: number;
  /** y of the jib; the mast reaches up to it. */
  top: number;
  /** How far the jib reaches to the right of the mast. */
  reach: number;
}

export interface Tower {
  x: number;
  width: number;
  floors: number;
  /** A tower still being built shows dashed slabs appearing above it. */
  building?: boolean;
  crane?: Crane;
}

export interface Window {
  x: number;
  y: number;
  width: number;
  delay: number;
  duration: number;
}

export interface FarBlock {
  x: number;
  y: number;
  width: number;
  height: number;
}

export const TOWERS: Tower[] = [
  { x: 40, width: 92, floors: 16 },
  { x: 160, width: 70, floors: 11 },
  { x: 250, width: 110, floors: 22, building: true, crane: { x: 374, top: 38, reach: 150 } },
  { x: 395, width: 84, floors: 14 },
  { x: 1010, width: 96, floors: 19 },
  { x: 1130, width: 120, floors: 24, building: true, crane: { x: 1264, top: 14, reach: 170 } },
  { x: 1280, width: 80, floors: 13 },
  { x: 1365, width: 70, floors: 17 },
];

/** Small seeded generator (mulberry32): the same seed always gives the same sequence. */
export function seededRandom(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export const towerTop = (tower: Tower): number => GROUND_Y - tower.floors * FLOOR_HEIGHT;

export const columnCount = (tower: Tower): number => Math.floor(tower.width / 16);

/** Roughly four windows in ten floors light up, each on its own rhythm. */
export function windowsFor(tower: Tower, random: () => number): Window[] {
  const columns = columnCount(tower);
  const cell = tower.width / columns;
  const top = towerTop(tower);
  const count = Math.round(tower.floors * 0.4);
  return Array.from({ length: count }, () => {
    const column = Math.floor(random() * columns);
    const row = Math.floor(random() * (tower.floors - 1));
    return {
      x: round(tower.x + 3 + column * cell),
      y: top + 3 + row * FLOOR_HEIGHT,
      width: round(cell - 6),
      delay: round(random() * 6),
      duration: round(3 + random() * 3),
    };
  });
}

/** The pale, slowly drifting skyline behind the towers. */
export function farBlocks(random: () => number): FarBlock[] {
  const blocks: FarBlock[] = [];
  for (let x = -40; x < SKY_WIDTH + 40; ) {
    const width = Math.round(50 + random() * 60);
    const height = Math.round(96 + random() * 104);
    blocks.push({ x, y: GROUND_Y - height, width, height });
    x += width + Math.round(5 + random() * 7);
  }
  return blocks;
}

export function round(value: number): number {
  return Math.round(value * 100) / 100;
}
