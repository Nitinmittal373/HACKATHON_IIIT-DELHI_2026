"use client";

import type { KeyboardEvent } from "react";

import {
  NODE_HEIGHT,
  NODE_WIDTH,
  truncate,
  type Layout,
  type Placed,
} from "@/lib/family";
import { useLang } from "@/lib/LangProvider";
import styles from "./FamilyTree.module.css";

interface Props {
  layout: Layout;
  selected: string | null;
  onSelect: (id: string) => void;
}

const LABEL_CHARS = 24;

/** The diagram. Every node is a button you can reach with Tab; edges are plain lines. */
export function FamilyTreeGraph({ layout, selected, onSelect }: Props) {
  const { t } = useLang();
  const byId = new Map(layout.nodes.map((node) => [node.id, node]));

  return (
    <svg
      className={styles.svg}
      viewBox={`0 0 ${layout.width} ${layout.height}`}
      role="group"
      aria-label={t.family.graphLabel}
    >
      <g aria-hidden="true">
        {layout.nodes.map((node) => {
          const parent = node.parent ? byId.get(node.parent) : undefined;
          return parent ? <Edge key={node.id} from={parent} to={node} /> : null;
        })}
      </g>
      {layout.nodes.map((node) => (
        <Node key={node.id} node={node} selected={selected === node.id} onSelect={onSelect} />
      ))}
    </svg>
  );
}

function Edge({ from, to }: { from: Placed; to: Placed }) {
  const x1 = from.x + NODE_WIDTH / 2;
  const y1 = from.y + NODE_HEIGHT;
  const x2 = to.x + NODE_WIDTH / 2;
  const middle = (y1 + to.y) / 2;
  return (
    <path
      className={`${styles.edge} ${to.kind === "company" ? styles.related : ""}`}
      d={`M ${x1} ${y1} C ${x1} ${middle}, ${x2} ${middle}, ${x2} ${to.y}`}
    />
  );
}

function Node({
  node,
  selected,
  onSelect,
}: {
  node: Placed;
  selected: boolean;
  onSelect: (id: string) => void;
}) {
  const { t } = useLang();
  const flag = node.flag ? t.family.flags[node.flag] : null;
  const second = flag ?? node.sub ?? (node.kind === "company" ? t.family.statusUnknown : "");

  function onKey(event: KeyboardEvent<SVGGElement>) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onSelect(node.id);
    }
  }

  return (
    <g
      className={`${styles.node} ${selected ? styles.selected : ""}`}
      data-flag={node.flag ?? "none"}
      transform={`translate(${node.x} ${node.y})`}
      role="button"
      tabIndex={0}
      aria-pressed={selected}
      aria-label={t.family.node(t.family.kinds[node.kind], node.label, flag)}
      onClick={() => onSelect(node.id)}
      onKeyDown={onKey}
    >
      <rect className={styles.box} width={NODE_WIDTH} height={NODE_HEIGHT} rx={12} />
      <text className={styles.name} x={12} y={24}>
        {truncate(node.label, LABEL_CHARS)}
      </text>
      <text className={`${styles.sub} ${flag ? styles.flagText : ""}`} x={12} y={44}>
        {truncate(second, LABEL_CHARS + 2)}
      </text>
    </g>
  );
}
