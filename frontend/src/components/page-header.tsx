import type { ReactNode } from "react";

export function PageHeader({ title, sub, actions }: { title: ReactNode; sub?: ReactNode; actions?: ReactNode }) {
  return (
    <header className="no-print flex flex-wrap items-center gap-3 border-b border-line bg-surface px-5 py-4 sm:px-7">
      <div className="min-w-0">
        <div className="text-lg font-bold tracking-tight">{title}</div>
        {sub && <div className="text-[13px] text-faint">{sub}</div>}
      </div>
      <div className="flex-1" />
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </header>
  );
}
