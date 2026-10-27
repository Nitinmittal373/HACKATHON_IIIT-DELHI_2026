"use client";

import { signIn } from "next-auth/react";
import Link from "next/link";

import { useAccount } from "@/lib/account";
import { useLang } from "@/lib/LangProvider";
import styles from "./LoginCard.module.css";

/** Sign in with Google (then on to `next`, a path on this site), a plain note that no account is needed to check, and what is kept. */
export function LoginCard({ enabled, next }: { enabled: boolean; next: string }) {
  const { t } = useLang();
  const account = useAccount();
  const copy = t.account.login;

  return (
    <section className={styles.card} aria-labelledby="login-title">
      <h1 id="login-title" className={styles.title}>
        {copy.title}
      </h1>
      <p className={styles.lead}>{copy.lead}</p>

      {account.status === "in" ? (
        <>
          <p className={styles.note}>{copy.signedIn(account.user.name ?? account.user.email ?? "")}</p>
          <Link href="/reports" className="btn">
            {copy.toReports}
          </Link>
        </>
      ) : (
        <>
          <button
            type="button"
            className={`btn ${styles.google}`}
            disabled={!enabled}
            onClick={() => void signIn("google", { callbackUrl: next })}
          >
            <GoogleMark />
            {copy.google}
          </button>
          {!enabled && <p className={styles.note}>{copy.off}</p>}
        </>
      )}

      <p className={styles.note}>{copy.notNeeded}</p>
      <p className={styles.privacy}>
        {copy.privacy}{" "}
        <Link href="/privacy">{t.privacy.loginLink}</Link>
      </p>
    </section>
  );
}

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path
        fill="currentColor"
        d="M21.35 11.1H12v2.9h5.35c-.5 2.4-2.55 3.6-5.35 3.6a5.6 5.6 0 0 1 0-11.2c1.4 0 2.65.5 3.6 1.4l2.1-2.1A8.5 8.5 0 0 0 12 3.5a8.5 8.5 0 1 0 0 17c4.9 0 8.4-3.4 8.4-8.3 0-.6-.05-1.1-.15-1.6z"
      />
    </svg>
  );
}
