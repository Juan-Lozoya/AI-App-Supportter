import type { ReactNode } from "react";

interface PanelProps {
  title: string;
  description?: string;
  children: ReactNode;
}

export function Panel({ title, description, children }: PanelProps) {
  return (
    <section className="mb-5 rounded-xl border border-line bg-white p-6">
      <h2 className="mb-2 text-lg font-bold">{title}</h2>
      {description && (
        <p className="mb-5 text-[13px] text-muted">{description}</p>
      )}
      {children}
    </section>
  );
}

// Fila título + texto, como `.result-item` del mockup.
export function ResultItem({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="border-b border-[#edf0f4] py-4 last:border-b-0">
      <div className="mb-1.5 text-sm font-bold">{title}</div>
      <div className="text-[13px] leading-relaxed text-muted">{children}</div>
    </div>
  );
}
