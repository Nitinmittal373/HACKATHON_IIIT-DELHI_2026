import type { Metadata, Viewport } from "next";
import localFont from "next/font/local";
import type { ReactNode } from "react";

import { AccountProvider } from "@/lib/account";
import { authConfigured } from "@/lib/authOptions";
import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { getLang } from "@/lib/i18n/server";
import { LangProvider } from "@/lib/LangProvider";
import { loadMeta } from "@/lib/meta";
import { MetaProvider } from "@/lib/MetaProvider";
import "@/styles/tokens.css";
import "@/styles/globals.css";
import "@/styles/app.css";
import "@/styles/print.css";

// Self-hosted so a build never depends on fonts.googleapis.com. All three files are variable
// fonts (licences next to them), so one file serves every weight listed here.
const geist = localFont({
  src: "../fonts/Geist-latin.woff2",
  weight: "100 900",
  variable: "--font-geist",
  display: "optional",
});
const geistMono = localFont({
  src: "../fonts/GeistMono-latin.woff2",
  weight: "400 500",
  variable: "--font-geist-mono",
  display: "swap",
  preload: false,
});
const devanagari = localFont({
  src: "../fonts/NotoSansDevanagari-devanagari.woff2",
  weight: "500 700",
  variable: "--font-devanagari",
  display: "swap",
  preload: false,
});

export const metadata: Metadata = {
  // Share previews need absolute addresses; set NEXT_PUBLIC_SITE_URL to the deployed site.
  metadataBase: new URL(process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000"),
  title: "NeevCheck: know your builder before you book",
  description:
    "A risk check for under-construction homes in Uttar Pradesh. TinyFish agents read UP-RERA, company, insolvency and court records and give a NeevScore with proof for every point.",
};

export const viewport: Viewport = { themeColor: "#ffffff" };

export default async function RootLayout({ children }: { children: ReactNode }) {
  const [lang, meta] = await Promise.all([getLang(), loadMeta()]);
  return (
    <html lang={lang} className={`${geist.variable} ${geistMono.variable} ${devanagari.variable}`}>
      <body>
        <LangProvider initial={lang}>
          <MetaProvider meta={meta}>
            <AccountProvider enabled={authConfigured()}>
              <Header />
              {children}
            </AccountProvider>
            <Footer />
          </MetaProvider>
        </LangProvider>
      </body>
    </html>
  );
}
