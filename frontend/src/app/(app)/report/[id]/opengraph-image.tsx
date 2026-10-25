import { ImageResponse } from "next/og";

import { ApiError, getReport } from "@/lib/api";
import { CHECK_ID_PATTERN } from "@/lib/ids";

export const alt = "NeevCheck report";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

const BAND_LABELS = {
  Low: "Low risk",
  Moderate: "Moderate risk",
  High: "High risk",
  Critical: "Critical risk",
  insufficient_evidence: "Not enough evidence yet",
} as const;

/** The picture shown when a report link is shared: project, score and band. */
export default async function Image({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let name = "NeevCheck";
  let score = "";
  let band = "Know your builder before you book.";
  if (CHECK_ID_PATTERN.test(id)) {
    try {
      const report = await getReport(id);
      name = report.project.name ?? report.project.rera_id;
      score = String(report.score.value);
      band = BAND_LABELS[report.score.band];
    } catch (error) {
      if (!(error instanceof ApiError)) throw error;
    }
  }

  return new ImageResponse(
    (
      <div
        style={{
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "space-between",
          padding: 72,
          background: "#FFF5EC",
          fontFamily: "sans-serif",
          color: "#111111",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", fontSize: 34, fontWeight: 700 }}>
          <div style={{ width: 44, height: 44, borderRadius: 11, background: "#F26B1D", marginRight: 16 }} />
          NeevCheck
        </div>
        <div style={{ display: "flex", flexDirection: "column" }}>
          <div style={{ fontSize: 60, fontWeight: 700, lineHeight: 1.1, maxWidth: 900 }}>{name}</div>
          <div style={{ display: "flex", alignItems: "baseline", marginTop: 28 }}>
            {score && <div style={{ fontSize: 150, fontWeight: 700, color: "#F26B1D" }}>{score}</div>}
            {score && <div style={{ fontSize: 40, color: "#5F5F5F", marginLeft: 12 }}>/ 100</div>}
            <div style={{ fontSize: 44, fontWeight: 600, marginLeft: score ? 36 : 0 }}>{band}</div>
          </div>
        </div>
        <div style={{ fontSize: 26, color: "#5F5F5F" }}>Public records, read by TinyFish agents</div>
      </div>
    ),
    size,
  );
}
