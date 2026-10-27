"use client";

import { SessionProvider, useSession } from "next-auth/react";
import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";

import { listChecksOfAccount } from "@/lib/accountReports";
import { setAccountSaver } from "@/lib/history";

export interface AccountUser {
  name: string | null;
  email: string | null;
  image: string | null;
}

/** "off": this deployment has no Google sign-in. "out": nobody is signed in. */
export type Account = { status: "off" | "loading" | "out" } | { status: "in"; user: AccountUser };

const AccountContext = createContext<Account>({ status: "off" });

/** Who is signed in. Without Google settings every visitor is simply signed out and unaffected. */
export function useAccount(): Account {
  return useContext(AccountContext);
}

export function AccountProvider({ enabled, children }: { enabled: boolean; children: ReactNode }) {
  if (!enabled) return <AccountContext.Provider value={{ status: "out" }}>{children}</AccountContext.Provider>;
  return (
    <SessionProvider refetchOnWindowFocus={false}>
      <SessionAccount>{children}</SessionAccount>
    </SessionProvider>
  );
}

function SessionAccount({ children }: { children: ReactNode }) {
  const { data, status } = useSession();
  const user = data?.user;
  const account = useMemo<Account>(() => {
    if (status === "loading") return { status: "loading" };
    if (status === "authenticated" && user) {
      return { status: "in", user: { name: user.name ?? null, email: user.email ?? null, image: user.image ?? null } };
    }
    return { status: "out" };
  }, [status, user]);

  const signedIn = account.status === "in";
  useEffect(() => {
    // While signed in, new checks are saved to the account; this browser's list moves over once.
    if (!signedIn) {
      setAccountSaver(null);
      return;
    }
    return listChecksOfAccount();
  }, [signedIn]);

  return <AccountContext.Provider value={account}>{children}</AccountContext.Provider>;
}
