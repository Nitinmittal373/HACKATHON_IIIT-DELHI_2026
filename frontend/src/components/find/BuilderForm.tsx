"use client";

import { useRouter } from "next/navigation";
import { useId, type FormEvent } from "react";

import { useLang } from "@/lib/LangProvider";
import styles from "./MoreWays.module.css";

/** A builder's name (and a city) in; that builder's registered projects out. */
export function BuilderForm() {
  const router = useRouter();
  const { t } = useLang();
  const nameId = useId();
  const cityId = useId();
  const copy = t.find.more.builder;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const builder = String(data.get("builder") ?? "").trim();
    const city = String(data.get("city") ?? "").trim();
    const place = city ? `&city=${encodeURIComponent(city)}` : "";
    router.push(`/check?builder=${encodeURIComponent(builder)}${place}`);
  }

  return (
    <form className={styles.form} onSubmit={submit}>
      <div className={styles.row}>
        <label className={styles.field} htmlFor={nameId}>
          {copy.label}
          <input id={nameId} name="builder" required minLength={3} maxLength={120} placeholder={copy.placeholder} autoComplete="off" />
        </label>
        <label className={styles.field} htmlFor={cityId}>
          {copy.cityLabel}
          <input id={cityId} name="city" maxLength={80} placeholder={copy.cityPlaceholder} autoComplete="off" />
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
