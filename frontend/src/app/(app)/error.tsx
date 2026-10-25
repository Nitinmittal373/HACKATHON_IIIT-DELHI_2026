"use client";

import Link from "next/link";

import { PageMessage } from "@/components/PageMessage";
import { useLang } from "@/lib/LangProvider";

/** Anything unexpected on an app screen ends here, with a way to try again. */
export default function AppError({ reset }: { error: Error; reset: () => void }) {
  const { t } = useLang();
  return (
    <PageMessage
      alert
      title={t.errors.somethingTitle}
      actions={
        <>
          <button type="button" className="btn" onClick={reset}>
            {t.common.tryAgain}
          </button>
          <Link href="/" className="btn2">
            {t.common.home}
          </Link>
        </>
      }
    >
      {t.errors.somethingBody}
    </PageMessage>
  );
}
