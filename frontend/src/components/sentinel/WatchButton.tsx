"use client";

import { useState } from "react";

import { WatchDialog } from "@/components/sentinel/WatchDialog";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";

interface Props {
  project: Pick<Project, "rera_id" | "details_url" | "state">;
  /** "primary" is the orange header button; "card" is the white button on the orange card. */
  look?: "primary" | "card";
}

export function WatchButton({ project, look = "primary" }: Props) {
  const { t } = useLang();
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        className={look === "primary" ? "btn" : "btn2"}
        style={look === "card" ? { color: "var(--o-text)", borderColor: "#fff" } : undefined}
        onClick={() => setOpen(true)}
      >
        {t.sentinel.open}
      </button>
      <WatchDialog project={project} open={open} onClose={() => setOpen(false)} />
    </>
  );
}
