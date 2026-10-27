import type { Metadata } from "next";

import { PageMessage } from "@/components/PageMessage";
import { StopAlerts } from "@/components/sentinel/StopAlerts";
import { getStrings } from "@/lib/i18n/server";

// The token is a secret; keep it out of the Referer header of anything this page links to.
export const metadata: Metadata = {
  title: "Stop alerts · NeevCheck",
  referrer: "no-referrer",
  robots: { index: false },
};

interface Props {
  searchParams: Promise<{ token?: string | string[] }>;
}

/** The page behind the link in every alert email. Opening it changes nothing; the button does. */
export default async function StopAlertsPage({ searchParams }: Props) {
  const raw = (await searchParams).token;
  const token = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";
  const { t } = await getStrings();

  if (!token) {
    return (
      <PageMessage title={t.alerts.stop.missingTitle}>{t.alerts.stop.missing}</PageMessage>
    );
  }
  return <StopAlerts token={token} />;
}
