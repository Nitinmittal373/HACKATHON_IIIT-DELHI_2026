"use client";

import Link from "next/link";

import { useAccount } from "@/lib/account";
import { useLang } from "@/lib/LangProvider";
import styles from "./SignInHint.module.css";

/** A small link under the search box; gone once someone is signed in. */
export function SignInHint({ className }: { className?: string }) {
  const account = useAccount();
  const { t } = useLang();
  if (account.status === "in") return null;
  return (
    <p className={`${styles.hint} ${className ?? ""}`} style={{ animationDelay: "0.52s" }}>
      <Link href="/login">{t.account.heroLink}</Link>
    </p>
  );
}
