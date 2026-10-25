import type { ReactNode } from "react";

import { Skyline } from "@/components/Skyline";

/** Every app screen sits in front of the same quiet, animated construction skyline. */
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <Skyline variant="app" />
      <main className="wrap appMain">{children}</main>
    </>
  );
}
