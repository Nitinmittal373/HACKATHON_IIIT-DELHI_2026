import * as React from "react";

import { cn, type Tone } from "@/lib/utils";

export function Card({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("rounded-2xl border border-line bg-surface", className)} {...props} />;
}

const TONES: Record<Tone, string> = {
  high: "bg-high-bg text-high-fg border-high-line",
  warn: "bg-warn-bg text-warn-fg border-warn-line",
  ok: "bg-ok-bg text-ok-fg border-ok-line",
  info: "bg-info-bg text-info-fg border-info-line",
  neutral: "bg-surface-2 text-muted border-line",
};

export function Badge({ tone = "neutral", className, ...props }: React.HTMLAttributes<HTMLSpanElement> & { tone?: Tone }) {
  return (
    <span
      className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border px-2.5 py-0.5 text-xs font-semibold", TONES[tone], className)}
      {...props}
    />
  );
}

export function Eyebrow({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("font-mono text-[11px] uppercase tracking-[0.08em] text-faint", className)} {...props} />;
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden className={cn("shimmer rounded-lg", className)} />;
}

export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input
      ref={ref}
      className={cn("w-full min-w-0 bg-transparent text-fg placeholder:text-faint outline-none", className)}
      {...props}
    />
  ),
);
Input.displayName = "Input";

export function Bar({ value, color, className }: { value: number; color?: string; className?: string }) {
  return (
    <div className={cn("h-1.5 overflow-hidden rounded-full bg-track", className)}>
      <div
        className="h-full rounded-full transition-[width] duration-1000 ease-out"
        style={{ width: `${Math.max(0, Math.min(100, value))}%`, background: color ?? "var(--accent)" }}
      />
    </div>
  );
}

export function EmptyState({ icon, title, children }: { icon?: React.ReactNode; title: string; children?: React.ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-line-strong bg-bg-2 px-6 py-14 text-center">
      {icon && <div className="text-faint [&_svg]:size-8">{icon}</div>}
      <div className="text-lg font-semibold">{title}</div>
      {children && <div className="max-w-md text-sm text-muted">{children}</div>}
    </div>
  );
}

export function ErrorNote({ children }: { children: React.ReactNode }) {
  return (
    <div role="alert" className="rounded-xl border border-high-line bg-high-soft px-4 py-3 text-sm text-high-fg">
      {children}
    </div>
  );
}
