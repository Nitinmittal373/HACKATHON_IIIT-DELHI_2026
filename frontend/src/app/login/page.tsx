import type { Metadata } from "next";

import { LoginCard } from "@/components/LoginCard";
import { Skyline } from "@/components/Skyline";
import { authConfigured } from "@/lib/authOptions";
import styles from "./login.module.css";

export const metadata: Metadata = { title: "Sign in · NeevCheck" };

/** A glass card over the skyline. Signing in is optional: checking a project never needs it. */
export default function LoginPage() {
  return (
    <>
      <Skyline variant="app" />
      <main className={`wrap appMain ${styles.page}`}>
        <LoginCard enabled={authConfigured()} />
      </main>
    </>
  );
}
