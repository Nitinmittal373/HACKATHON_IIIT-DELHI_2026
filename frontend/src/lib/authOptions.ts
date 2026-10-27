import type { NextAuthOptions } from "next-auth";
import GoogleProvider, { type GoogleProfile } from "next-auth/providers/google";

/** Sign-in is offered only when the deployment has been given all three Google settings. */
export function authConfigured(): boolean {
  return Boolean(process.env.AUTH_SECRET && process.env.AUTH_GOOGLE_ID && process.env.AUTH_GOOGLE_SECRET);
}

// Only the Google account id, name, e-mail and picture are read; nothing is stored by the site.
export const authOptions: NextAuthOptions = {
  secret: process.env.AUTH_SECRET,
  session: { strategy: "jwt" },
  pages: { signIn: "/login" },
  providers: [
    GoogleProvider({
      clientId: process.env.AUTH_GOOGLE_ID ?? "",
      clientSecret: process.env.AUTH_GOOGLE_SECRET ?? "",
    }),
  ],
  callbacks: {
    // Alerts go to the account's email, so only a Google-verified address may sign in.
    signIn({ account, profile }) {
      if (account?.provider !== "google") return false;
      return (profile as GoogleProfile | undefined)?.email_verified === true;
    },
    session({ session, token }) {
      // The Google account id is the token's subject; the API names the account by it.
      if (session.user && token.sub) session.user.id = token.sub;
      return session;
    },
  },
};
