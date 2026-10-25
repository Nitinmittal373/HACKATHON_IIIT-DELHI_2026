import Link from "next/link";

import { PageMessage } from "@/components/PageMessage";
import type { ApiError } from "@/lib/api";
import { getStrings } from "@/lib/i18n/server";

/** A calm message for a page whose data could not be loaded, with a link to try again. */
export async function ApiProblem({ error, retryHref }: { error: ApiError; retryHref: string }) {
  const { t } = await getStrings();
  const unreachable = error.status === 0;
  return (
    <PageMessage
      alert
      title={unreachable ? t.errors.unreachableTitle : t.errors.somethingTitle}
      actions={
        <Link href={retryHref} className="btn">
          {t.common.tryAgain}
        </Link>
      }
    >
      {unreachable ? t.errors.unreachableBody : t.errors.somethingBody}
    </PageMessage>
  );
}
