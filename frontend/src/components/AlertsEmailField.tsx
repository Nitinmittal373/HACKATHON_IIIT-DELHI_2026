"use client";

import { useAccount } from "@/lib/account";
import { useLang } from "@/lib/LangProvider";

/** The Alerts e-mail box; for a signed-in visitor it starts as their account's address. */
export function AlertsEmailField({ email, className }: { email: string; className: string }) {
  const account = useAccount();
  const { t } = useLang();
  const own = account.status === "in" ? (account.user.email ?? "") : "";
  return (
    <input
      // A new account address restarts the field; the visitor can still type another one.
      key={own}
      id="alerts-email"
      name="email"
      type="email"
      className={className}
      placeholder={t.sentinel.emailPlaceholder}
      defaultValue={email || own}
      maxLength={254}
      required
    />
  );
}
