"use client";

import { useId, useState } from "react";

import { safeHref } from "@/lib/utils";

/** Drawn towers-and-crane illustration. Labelled as an illustration wherever it is used. */
export function TowersIllustration({ className }: { className?: string }) {
  const id = useId().replace(/:/g, "");
  return (
    <svg className={className} viewBox="0 0 520 300" preserveAspectRatio="xMidYMid slice" role="img" aria-label="Illustration of residential towers with a crane">
      <defs>
        <linearGradient id={`sky${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" style={{ stopColor: "var(--sky-1)" }} />
          <stop offset="1" style={{ stopColor: "var(--sky-2)" }} />
        </linearGradient>
        <pattern id={`win${id}`} width="14" height="16" patternUnits="userSpaceOnUse">
          <rect x="3" y="4" width="7" height="8" rx="1" style={{ fill: "var(--win)" }} />
        </pattern>
      </defs>
      <rect width="520" height="300" fill={`url(#sky${id})`} />
      <circle cx="430" cy="70" r="26" style={{ fill: "var(--sun)" }} opacity=".85" />
      {[[18, 110, 70], [96, 140, 56], [352, 100, 64], [430, 130, 80]].map(([x, y, w]) => (
        <rect key={x} x={x} y={y} width={w} height={300 - y} style={{ fill: "var(--bld-1)" }} />
      ))}
      {[[150, 56, 84], [246, 98, 78]].map(([x, y, w]) => (
        <g key={x}>
          <rect x={x} y={y} width={w} height={300 - y} style={{ fill: "var(--bld-2)" }} />
          <rect x={x} y={y} width={w} height={300 - y} fill={`url(#win${id})`} />
        </g>
      ))}
      <rect x="336" y="170" width="60" height="130" style={{ fill: "var(--bld-2)" }} opacity=".75" />
      <path d="M366 170 V24 M330 30 H452 M366 24 L330 30 M366 24 L452 30 M440 30 V70" style={{ stroke: "var(--sun)" }} strokeWidth="3" fill="none" />
      <rect x="0" y="282" width="520" height="18" style={{ fill: "var(--ground)" }} />
      {[[40, 12], [118, 10], [470, 12]].map(([x, r]) => (
        <circle key={x} cx={x} cy={282} r={r} style={{ fill: "var(--tree)" }} />
      ))}
    </svg>
  );
}

/**
 * The project's own photo from its UP-RERA page when the agent found one; otherwise the drawn illustration.
 * Government image links can break or block hot-linking, so a failed load falls back to the illustration.
 */
export function ProjectPhoto({ src, sourceUrl, className }: { src: string | null; sourceUrl: string | null; className?: string }) {
  return <ProjectPhotoInner key={src ?? "none"} src={src} sourceUrl={sourceUrl} className={className} />;
}

function ProjectPhotoInner({ src, sourceUrl, className }: { src: string | null; sourceUrl: string | null; className?: string }) {
  const [failed, setFailed] = useState(false);
  const show = !!src && !!safeHref(src) && !failed;
  return (
    <figure className={`relative m-0 overflow-hidden rounded-2xl border border-line ${className ?? ""}`}>
      {show ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src!} alt="Project photo from its UP-RERA page" referrerPolicy="no-referrer" onError={() => setFailed(true)} className="absolute inset-0 size-full object-cover" />
      ) : (
        <TowersIllustration className="absolute inset-0 size-full" />
      )}
      <figcaption className="absolute bottom-3 left-3 rounded-lg bg-black/60 px-2.5 py-1.5 text-xs text-white backdrop-blur">
        {show ? "Photo from the UP-RERA page" : "Illustration · no photo on the UP-RERA page"}
        {sourceUrl && <> · <a href={safeHref(sourceUrl)} target="_blank" rel="noopener noreferrer" className="underline">source</a></>}
      </figcaption>
    </figure>
  );
}
