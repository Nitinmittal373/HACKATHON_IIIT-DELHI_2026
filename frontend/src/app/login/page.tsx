import type { Metadata } from "next";

import { LoginCard } from "@/components/LoginCard";
import { Skyline } from "@/components/Skyline";
import { authConfigured } from "@/lib/authOptions";
import { safeNext } from "@/lib/safeNext";
import styles from "./login.module.css";

export const metadata: Metadata = { title: "Sign in · NeevCheck" };

/**
 * A glass card over the skyline. Signing in is optional: checking a project never needs it.
 * `next` says where to go afterwards (the home page by default); only a path on this site counts.
 */
export default async function LoginPage({ searchParams }: { searchParams: Promise<{ next?: string }> }) {
  const { next } = await searchParams;
  return (
    <>
      <Skyline variant="app" />
      <main className={`wrap appMain ${styles.page}`}>
        <LoginCard enabled={authConfigured()} next={safeNext(next)} />
      </main>
    </>
  );
}
