import Link from "next/link";

import { PageMessage } from "@/components/PageMessage";
import { getStrings } from "@/lib/i18n/server";

/** Any address that matches no page. */
export default async function NotFound() {
  const { t } = await getStrings();
  return (
    <main className="wrap appMain">
      <PageMessage
        title={t.errors.notFoundTitle}
        actions={
          <Link href="/" className="btn">
            {t.common.home}
          </Link>
        }
      >
        {t.errors.notFoundBody}
      </PageMessage>
    </main>
  );
}
