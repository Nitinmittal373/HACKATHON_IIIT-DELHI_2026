import type { MetadataRoute } from "next";

const SITE = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
const PAGES = ["/", "/check", "/how-it-works", "/rwa", "/alerts", "/privacy", "/login"];

/** Every public page. Reports and live checks belong to the people who ran them, so they are left out. */
export default function sitemap(): MetadataRoute.Sitemap {
  return PAGES.map((path) => ({ url: new URL(path, SITE).toString() }));
}
