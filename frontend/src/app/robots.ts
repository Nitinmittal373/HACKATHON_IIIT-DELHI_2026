import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/site";

/** Everything public may be indexed; the sitemap lists the pages worth finding. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: { userAgent: "*", allow: "/" },
    sitemap: new URL("/sitemap.xml", SITE_URL).toString(),
  };
}
