import Link from "next/link";

import { PageMessage } from "@/components/PageMessage";
import { getStrings } from "@/lib/i18n/server";

export default async function AppNotFound() {
  const { t } = await getStrings();
  return (
    <PageMessage
      title={t.errors.notFoundTitle}
      actions={
        <Link href="/check" className="btn">
          {t.hero.submit}
        </Link>
      }
    >
      {t.errors.notFoundBody}
    </PageMessage>
  );
}
