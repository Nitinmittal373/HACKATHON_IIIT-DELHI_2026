"use client";

import { useRouter } from "next/navigation";
import { useId, type FormEvent } from "react";

import { useLang } from "@/lib/LangProvider";
import styles from "./MoreWays.module.css";

/** A project name plus the city or locality it is in, which also picks the state's portal. */
export function LocalityForm() {
  const router = useRouter();
  const { t } = useLang();
  const nameId = useId();
  const placeId = useId();
  const copy = t.find.more.locality;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const name = String(data.get("name") ?? "").trim();
    const locality = String(data.get("locality") ?? "").trim();
    router.push(`/check?q=${encodeURIComponent(name)}&locality=${encodeURIComponent(locality)}`);
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <div className={styles.row}>
        <label className={styles.field} htmlFor={nameId}>
          {copy.nameLabel}
          <input id={nameId} name="name" required minLength={2} maxLength={100} placeholder={copy.namePlaceholder} autoComplete="off" />
        </label>
        <label className={styles.field} htmlFor={placeId}>
          {copy.localityLabel}
          <input id={placeId} name="locality" required maxLength={80} placeholder={copy.localityPlaceholder} autoComplete="off" />
        </label>
      </div>
      <p className={styles.help}>{copy.help}</p>
      <div className={styles.actions}>
        <button type="submit" className="btn">
          {copy.submit}
        </button>
      </div>
    </form>
  );
}
