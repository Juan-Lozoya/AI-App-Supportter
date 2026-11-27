import type { ReactNode } from "react";

import type { Tone } from "../lib/format";

const tones: Record<Tone, string> = {
  amber: "bg-amber-100 text-amber-700",
  green: "bg-green-100 text-green-800",
  red: "bg-red-100 text-red-700",
  slate: "bg-slate-100 text-slate-600",
  sky: "bg-sky-100 text-sky-800",
};

export function Badge({ tone, children }: { tone: Tone; children: ReactNode }) {
  return (
    <span
      className={`inline-block rounded-full px-2.5 py-1.5 text-xs font-bold ${tones[tone]}`}
    >
      {children}
    </span>
  );
}
