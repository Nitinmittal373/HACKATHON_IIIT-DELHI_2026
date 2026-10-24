"use client";

import "@xyflow/react/dist/style.css";

import { Background, Controls, Handle, Position, ReactFlow, type Edge, type Node, type NodeProps } from "@xyflow/react";
import { useMemo } from "react";

import type { GraphEdge, GraphNode } from "@/lib/types";
import { cn } from "@/lib/utils";

type Data = { node: GraphNode };

function EntityNode({ data }: NodeProps<Node<Data>>) {
  const n = data.node;
  return (
    <div
      className={cn(
        "w-[210px] rounded-2xl border px-4 py-3 text-center shadow-sm",
        n.risk === "high" ? "border-high-line bg-high-bg text-high-fg"
          : n.risk === "review" ? "border-warn-line bg-warn-bg text-warn-fg"
            : "border-line-strong bg-surface-2 text-fg",
      )}
    >
      <Handle type="target" position={Position.Top} className="!size-1.5 !border-0 !bg-line-strong" />
      <div className="font-mono text-[10px] uppercase tracking-wider opacity-70">{n.kind === "promoter" ? "Promoter" : n.kind === "project" ? "Project" : "Possible group company"}</div>
      <div className="mt-1 text-[13px] font-bold leading-tight">{n.label}</div>
      <div className="mt-1 text-[11px] leading-tight opacity-80">{n.status}</div>
      <Handle type="source" position={Position.Bottom} className="!size-1.5 !border-0 !bg-line-strong" />
    </div>
  );
}

const nodeTypes = { entity: EntityNode };

export function FamilyTree({ nodes, edges }: { nodes: GraphNode[]; edges: GraphEdge[] }) {
  const { rfNodes, rfEdges } = useMemo(() => {
    const children = nodes.filter((n) => n.kind !== "promoter");
    const gap = 250;
    const startX = -((children.length - 1) * gap) / 2;
    const rfNodes: Node<Data>[] = nodes.map((n) => ({
      id: n.id,
      type: "entity",
      data: { node: n },
      position: n.kind === "promoter" ? { x: -105, y: 0 } : { x: startX + children.indexOf(n) * gap - 105, y: 170 },
    }));
    const rfEdges: Edge[] = edges.map((e, i) => ({
      id: `e${i}`,
      source: e.source,
      target: e.target,
      label: e.label,
      animated: !e.verified,
      style: { strokeDasharray: e.verified ? undefined : "6 6", strokeWidth: 1.5 },
      labelStyle: { fontSize: 11, fill: "var(--faint)" },
      labelBgStyle: { fill: "var(--surface)" },
    }));
    return { rfNodes, rfEdges };
  }, [nodes, edges]);

  if (!nodes.length) {
    return <p className="text-sm text-muted">The promoter could not be identified in this run, so no family tree was drawn.</p>;
  }
  return (
    <div className="h-[360px] w-full overflow-hidden rounded-xl border border-line bg-bg-2">
      <ReactFlow
        nodes={rfNodes} edges={rfEdges} nodeTypes={nodeTypes} fitView fitViewOptions={{ padding: 0.25 }}
        nodesConnectable={false} elementsSelectable={false} panOnScroll={false} zoomOnScroll={false}
        aria-label="Builder family tree"
      >
        <Background gap={22} size={1} color="var(--line)" />
        <Controls showInteractive={false} className="!shadow-none" />
      </ReactFlow>
    </div>
  );
}
