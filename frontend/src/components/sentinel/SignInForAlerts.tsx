"use client";

import Link from "next/link";

import { useLang } from "@/lib/LangProvider";

/**
 * Alerts belong to an account, so a visitor who is not signed in is asked to sign in first.
 * `next` is the page to come back to afterwards; without it they land on the home page.
 */
export function SignInForAlerts({ className, next }: { className?: string; next?: string }) {
  const { t } = useLang();
  return (
    <div className={className}>
      <p>{t.sentinel.signInReason}</p>
      <Link href={next ? `/login?next=${encodeURIComponent(next)}` : "/login"} className="btn">
        {t.sentinel.signIn}
      </Link>
    </div>
  );
}
