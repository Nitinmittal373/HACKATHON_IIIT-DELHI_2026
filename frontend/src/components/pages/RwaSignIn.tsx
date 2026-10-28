"use client";

import Link from "next/link";

import { useAccount } from "@/lib/account";
import { useLang } from "@/lib/LangProvider";
import styles from "./pages.module.css";

/** Signed out: a prompt to sign in to watch. Signed in: where the watches and alerts are. */
export function RwaSignIn() {
  const account = useAccount();
  const { t } = useLang();
  const copy = t.pages.rwa;
  const signedIn = account.status === "in";

  return (
    <section className={styles.section} aria-label={copy.signIn}>
      <p className={styles.text}>{signedIn ? copy.signedInLead : copy.signInLead}</p>
      <div className={styles.actions}>
        {signedIn ? (
          <Link href="/alerts" className="btn">
            {copy.alerts}
          </Link>
        ) : (
          <Link href="/login?next=%2Falerts" className="btn">
            {copy.signIn}
          </Link>
        )}
        <Link href="/check" className="btn2">
          {copy.check}
        </Link>
      </div>
    </section>
  );
}
