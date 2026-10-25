import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono, Noto_Sans_Devanagari } from "next/font/google";
import type { ReactNode } from "react";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { getLang } from "@/lib/i18n/server";
import { LangProvider } from "@/lib/LangProvider";
import "@/styles/tokens.css";
import "@/styles/globals.css";
import "@/styles/app.css";
import "@/styles/print.css";

const geist = Geist({ subsets: ["latin"], variable: "--font-geist", display: "optional" });
const geistMono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-geist-mono",
  display: "swap",
  preload: false,
});
const devanagari = Noto_Sans_Devanagari({
  subsets: ["devanagari"],
  weight: ["500", "600", "700"],
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
  const lang = await getLang();
  return (
    <html lang={lang} className={`${geist.variable} ${geistMono.variable} ${devanagari.variable}`}>
      <body>
        <LangProvider initial={lang}>
          <Header />
          {children}
          <Footer />
        </LangProvider>
      </body>
    </html>
  );
}
