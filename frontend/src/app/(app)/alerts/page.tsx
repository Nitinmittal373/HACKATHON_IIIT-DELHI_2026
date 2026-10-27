import type { Metadata } from "next";

import { AccountAlerts } from "@/components/sentinel/AccountAlerts";
import { getStrings } from "@/lib/i18n/server";

export const metadata: Metadata = { title: "Alerts · NeevCheck" };

/** Alerts belong to the signed-in account, so the list is read in the browser with its token. */
export default async function AlertsPage() {
  const { t } = await getStrings();
  return (
    <>
      <h1 className="h2 pageTitle">{t.alerts.title}</h1>
      <p className="pageLead">{t.alerts.lead}</p>
      <AccountAlerts />
    </>
  );
}
