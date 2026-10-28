"use client";

import { signOut } from "next-auth/react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { Avatar } from "@/components/Avatar";
import { clearAccountData } from "@/lib/accountData";
import { deleteMyData } from "@/lib/accountReports";
import { useAccount } from "@/lib/account";
import { useLang } from "@/lib/LangProvider";
import styles from "./AccountMenu.module.css";

/** "Sign in" for a visitor; the Google avatar with My reports and Sign out once signed in. */
export function AccountMenu() {
  const account = useAccount();
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const [failed, setFailed] = useState(false);
  const box = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const close = (event: Event) => {
      if (event.target instanceof Node && !box.current?.contains(event.target)) setOpen(false);
    };
    const escape = (event: KeyboardEvent) => event.key === "Escape" && setOpen(false);
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", escape);
    return () => {
      document.removeEventListener("pointerdown", close);
      document.removeEventListener("keydown", escape);
    };
  }, [open]);

  async function deleteData() {
    if (!window.confirm(t.account.deleteConfirm)) return;
    setFailed(false);
    try {
      await deleteMyData();
    } catch {
      setFailed(true);
      return;
    }
    await leave();
  }

  /** Clears this browser of the account, then signs out; the redirect reloads the whole page. */
  async function leave() {
    clearAccountData();
    await signOut({ callbackUrl: "/" });
  }

  if (account.status !== "in") {
    return (
      <Link href="/login" className={`btn2 ${styles.signIn}`}>
        {t.account.signIn}
      </Link>
    );
  }

  const name = account.user.name ?? account.user.email ?? "";
  return (
    <div className={styles.box} ref={box}>
      <button
        type="button"
        className={styles.avatar}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t.account.menuLabel}
        onClick={() => setOpen((value) => !value)}
      >
        <Avatar src={account.user.image} name={name} label={t.account.menuLabel} size={36} />
      </button>
      {open && (
        <div className={styles.menu} role="menu">
          <p className={styles.who}>{name}</p>
          <Link href="/reports" role="menuitem" onClick={() => setOpen(false)}>
            {t.nav.reports}
          </Link>
          <button type="button" role="menuitem" onClick={() => void leave()}>
            {t.account.signOut}
          </button>
          <button type="button" role="menuitem" onClick={() => void deleteData()}>
            {t.account.deleteData}
          </button>
          {failed && (
            <p className={styles.who} role="alert">
              {t.account.deleteFailed}
            </p>
          )}
        </div>
      )}
    </div>
  );
}
