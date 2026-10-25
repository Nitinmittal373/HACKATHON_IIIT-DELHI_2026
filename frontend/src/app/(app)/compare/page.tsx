import type { Metadata } from "next";

import { CompareView } from "@/components/compare/CompareView";
import { CHECK_ID_PATTERN } from "@/lib/ids";

export const metadata: Metadata = { title: "Compare projects · NeevCheck" };

interface Props {
  searchParams: Promise<{ ids?: string | string[] }>;
}

/** /compare?ids=a,b,c. The comparison is fetched in the browser, like search. */
export default async function ComparePage({ searchParams }: Props) {
  const raw = (await searchParams).ids;
  const text = Array.isArray(raw) ? raw.join(",") : (raw ?? "");
  const ids = [...new Set(text.split(",").filter((id) => CHECK_ID_PATTERN.test(id)))].slice(0, 3);
  return <CompareView fromUrl={ids} />;
}
