import Link from "next/link";

import { PageMessage } from "@/components/PageMessage";
import type { Strings } from "@/lib/i18n";

export function EmptyResults({ query, t }: { query: string; t: Strings }) {
  return (
    <PageMessage
      title={t.confirm.emptyTitle}
      actions={
        <Link href="/#search" className="btn">
          {t.confirm.searchAgain}
        </Link>
      }
    >
      <p>{t.confirm.emptyBody(query)}</p>
      <p style={{ marginTop: 14, color: "var(--ink)", fontWeight: 600 }}>{t.confirm.tipsTitle}</p>
      <ul>
        {t.confirm.tips.map((tip) => (
          <li key={tip}>{tip}</li>
        ))}
      </ul>
    </PageMessage>
  );
}
