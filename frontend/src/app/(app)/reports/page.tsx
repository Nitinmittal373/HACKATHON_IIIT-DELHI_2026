import type { Metadata } from "next";

import { MyReports } from "@/components/reports/MyReports";

export const metadata: Metadata = { title: "My reports · NeevCheck" };

/** The list lives in the visitor's browser, so the whole page is drawn there. */
export default function ReportsPage() {
  return <MyReports />;
}
