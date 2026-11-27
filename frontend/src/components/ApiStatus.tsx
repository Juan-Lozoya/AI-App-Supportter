import type { ReactNode } from "react";

type State = "loading" | "success" | "error";

const styles: Record<State, string> = {
  loading: "bg-sky-100 text-sky-800",
  success: "bg-green-100 text-green-800",
  error: "bg-red-100 text-red-800",
};

interface ApiStatusProps {
  state: State;
  title: string;
  children?: ReactNode;
}

export function ApiStatus({ state, title, children }: ApiStatusProps) {
  return (
    <div
      role={state === "error" ? "alert" : "status"}
      aria-live="polite"
      className={`mt-4 rounded-lg p-4 text-sm leading-relaxed ${styles[state]}`}
    >
      <strong className="block">{title}</strong>
      {children}
    </div>
  );
}

// Para secciones que cargan con su propia consulta.
export function SectionState({ error }: { error: Error | null }) {
  if (error)
    return (
      <p role="alert" className="text-sm text-red-700">
        {error.message}
      </p>
    );
  return <p className="text-sm text-muted">Loading…</p>;
}
