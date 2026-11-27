import type { ReactNode } from "react";

import { REVIEWER } from "../lib/format";

interface HeaderProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}

export function Header({ title, subtitle, actions }: HeaderProps) {
  return (
    <header className="mb-8 flex flex-col items-start justify-between gap-4 md:flex-row md:items-center">
      <div>
        <h1 className="text-[26px] font-bold">{title}</h1>
        {subtitle && <p className="mt-1.5 text-muted">{subtitle}</p>}
      </div>
      <div className="flex flex-wrap items-center gap-3">
        {actions}
        <div className="rounded-[10px] border border-slate-200 bg-white px-[18px] py-3">
          {REVIEWER}
        </div>
      </div>
    </header>
  );
}
