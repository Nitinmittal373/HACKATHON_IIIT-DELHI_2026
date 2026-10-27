"use client";

import Link from "next/link";

import { useLang } from "@/lib/LangProvider";

/** Alerts belong to an account, so a visitor who is not signed in is asked to sign in first. */
export function SignInForAlerts({ className }: { className?: string }) {
  const { t } = useLang();
  return (
    <div className={className}>
      <p>{t.sentinel.signInReason}</p>
      <Link href="/login" className="btn">
        {t.sentinel.signIn}
      </Link>
    </div>
  );
}
