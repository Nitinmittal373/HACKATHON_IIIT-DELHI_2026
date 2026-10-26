import type { FamilyTree } from "@/lib/types";

export type NodeKind = "promoter" | "director" | "company" | "project";
/** What makes a node stand out. The label always says it in words; the outline is extra. */
export type NodeFlag = "cirp" | "struck_off" | "lapsed" | "delayed" | "unread";

export interface FamilyNode {
  id: string;
  kind: NodeKind;
  /** 0 promoter, 1 directors, 2 related companies, 3 projects. */
  tier: number;
  label: string;
  /** DIN, registry status or RERA number: the second line of the node. */
  sub: string | null;
  flag: NodeFlag | null;
  /** The node this one hangs from; null for the promoter. */
  parent: string | null;
  /** The page behind the node, when there is one. */
  href: string | null;
}

export interface Placed extends FamilyNode {
  x: number;
  y: number;
}

export interface Layout {
  nodes: Placed[];
  width: number;
  height: number;
}

export const NODE_WIDTH = 176;
export const NODE_HEIGHT = 58;
const GAP_X = 16;
const GAP_Y = 54;
const PER_ROW = 6;
const MARGIN = 8;

/** Every node of the tree, parents before children. */
export function familyNodes(tree: FamilyTree): FamilyNode[] {
  const nodes: FamilyNode[] = [
    {
      id: "promoter",
      kind: "promoter",
      tier: 0,
      label: tree.promoter,
      sub: null,
      flag: null,
      parent: null,
      href: tree.source_url,
    },
  ];
  tree.directors.forEach((director, index) =>
    nodes.push({
      id: `director-${index}`,
      kind: "director",
      tier: 1,
      label: director.name,
      sub: `DIN ${director.din}`,
      flag: null,
      parent: "promoter",
      href: null,
    }),
  );
  tree.companies.forEach((company, index) =>
    nodes.push({
      id: `company-${index}`,
      kind: "company",
      tier: 2,
      label: company.name,
      sub: company.status,
      flag: company.flag,
      parent: "promoter",
      href: company.status_url,
    }),
  );
  const projects = (parent: string, list: FamilyTree["promoter_projects"]) =>
    list.forEach((project) =>
      nodes.push({
        id: `project-${project.rera_id}`,
        kind: "project",
        tier: 3,
        label: project.name ?? project.rera_id,
        sub: project.rera_id,
        flag: project.state === "ok" ? null : project.state,
        parent,
        href: project.details_url,
      }),
    );
  projects("promoter", tree.promoter_projects);
  tree.companies.forEach((company, index) => projects(`company-${index}`, company.projects));
  return nodes;
}

/** A simple tiered layout: one band per tier, wrapped at six nodes a row, each row centred. */
export function layoutFamily(nodes: FamilyNode[]): Layout {
  const tiers = [0, 1, 2, 3].map((tier) => nodes.filter((node) => node.tier === tier));
  const widest = Math.min(PER_ROW, Math.max(1, ...tiers.map((tier) => tier.length)));
  const width = widest * NODE_WIDTH + (widest - 1) * GAP_X + 2 * MARGIN;
  const placed: Placed[] = [];
  let y = MARGIN;
  for (const tier of tiers) {
    for (let start = 0; start < tier.length; start += PER_ROW) {
      const row = tier.slice(start, start + PER_ROW);
      const rowWidth = row.length * NODE_WIDTH + (row.length - 1) * GAP_X;
      const left = (width - rowWidth) / 2;
      row.forEach((node, column) =>
        placed.push({ ...node, x: left + column * (NODE_WIDTH + GAP_X), y }),
      );
      y += NODE_HEIGHT + GAP_Y;
    }
  }
  return { nodes: placed, width, height: Math.max(y - GAP_Y + MARGIN, NODE_HEIGHT + 2 * MARGIN) };
}

export function truncate(text: string, max: number): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}
