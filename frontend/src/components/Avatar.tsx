"use client";

import { useState } from "react";

interface Props {
  /** The Google picture, when the account has one. */
  src: string | null;
  /** The name or e-mail the initials come from. */
  name: string;
  /** Alt text for the picture. */
  label: string;
  size: number;
}

/** "Asha Buyer" -> "AB"; one word gives one letter. */
export function initialsOf(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((word) => word.slice(0, 1).toUpperCase())
    .join("");
}

/**
 * The Google picture, or a round badge with the person's initials when there is none or it
 * does not load. A broken image or its alt text is never shown.
 */
export function Avatar({ src, name, label, size }: Props) {
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  if (!src || failedSrc === src) return <span aria-hidden="true">{initialsOf(name)}</span>;
  return (
    // A small remote Google picture; a plain img lets a failed load fall back to the initials.
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={label}
      width={size}
      height={size}
      referrerPolicy="no-referrer"
      onError={() => setFailedSrc(src)}
    />
  );
}
