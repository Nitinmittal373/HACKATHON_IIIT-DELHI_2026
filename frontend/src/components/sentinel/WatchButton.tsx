"use client";

import { useEffect, useState } from "react";

import { WatchDialog } from "@/components/sentinel/WatchDialog";
import { useAccount } from "@/lib/account";
import { useLang } from "@/lib/LangProvider";
import type { Project } from "@/lib/types";

interface Props {
  project: Pick<Project, "rera_id" | "details_url">;
  /** "primary" is the orange header button; "card" is the white button on the orange card. */
  look?: "primary" | "card";
}

export function WatchButton({ project, look = "primary" }: Props) {
  const { t } = useLang();
  const account = useAccount();
  const [open, setOpen] = useState(false);
  const signedIn = account.status === "in";

  useEffect(() => {
    // WatchDialog sends a visitor to sign in with ?watch=1. Back on this report: open the dialog again, once, and tidy the address.
    // Only the main button does it, so the second one on the page does not open a second dialog.
    if (!signedIn || look !== "primary") return;
    const url = new URL(window.location.href);
    if (url.searchParams.get("watch") !== "1") return;
    url.searchParams.delete("watch");
    window.history.replaceState(null, "", `${url.pathname}${url.search}${url.hash}`);
    setOpen(true);
  }, [signedIn, look]);

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
