"use client";

import { FileSearch, Plus } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { BandBadge } from "@/components/score";
import { Button } from "@/components/ui/button";
import { Badge, Card, EmptyState, ErrorNote, Skeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import { shortDate, titleCase } from "@/lib/utils";
import { useAsync } from "@/lib/use-async";

export default function ReportsPage() {
  const { data, error, loading } = useAsync(() => api.reports());
  return (
    <>
      <PageHeader title="Reports" sub="Every check is saved with its evidence and retrieval dates" actions={<Button asChild size="sm"><Link href="/check"><Plus /> New check</Link></Button>} />
      <main className="mx-auto max-w-[1180px] px-5 py-7 sm:px-7">
        {error && <ErrorNote>{error}</ErrorNote>}
        {loading ? <Skeleton className="h-64" /> : !data?.length ? (
          <EmptyState icon={<FileSearch />} title="No reports yet">Run a check and it will appear here.</EmptyState>
        ) : (
          <Card className="overflow-x-auto">
            <table className="w-full min-w-[720px] text-sm">
              <thead>
                <tr className="text-left font-mono text-[11px] uppercase tracking-wider text-faint">
                  <th className="px-5 py-3 font-medium">Project</th><th className="px-3 py-3 font-medium">Score</th><th className="px-3 py-3 font-medium">Band</th>
                  <th className="px-3 py-3 font-medium">Confidence</th><th className="px-3 py-3 font-medium">Checked</th><th className="px-5 py-3" />
                </tr>
              </thead>
              <tbody>
                {data.map((r) => (
                  <tr key={r.id} className="border-t border-line transition-colors hover:bg-surface-2">
                    <td className="px-5 py-3.5">
                      <Link href={`/reports/${r.id}`} className="font-semibold hover:underline">{titleCase(r.project_name) || r.query}</Link>
                      <div className="text-xs text-faint">{r.promoter_name ?? "Promoter not identified"}</div>
                    </td>
                    <td className="px-3 py-3.5 font-mono">{r.band === "Not enough data" ? "–" : r.score}</td>
                    <td className="px-3 py-3.5"><BandBadge band={r.band} /></td>
                    <td className="px-3 py-3.5 font-mono">{Math.round(r.confidence * 100)}%</td>
                    <td className="px-3 py-3.5 text-xs text-faint">{shortDate(r.created_at)}</td>
                    <td className="px-5 py-3.5 text-right">{r.watching && <Badge tone="ok">Watching</Badge>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        )}
      </main>
    </>
  );
}
