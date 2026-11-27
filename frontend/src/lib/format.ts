// Usuario fijo: el backend exige `reviewer` y todavía no hay autenticación.
export const REVIEWER = "Operations User";

export function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return "—";
  return ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
}

// Las fechas "YYYY-MM-DD" se leen como fecha local para evitar el desfase de zona horaria.
export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const dateOnly = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value);
  const date = dateOnly
    ? new Date(
        Number(dateOnly[1]),
        Number(dateOnly[2]) - 1,
        Number(dateOnly[3]),
      )
    : new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

// "CASH_DIVIDEND" -> "Cash dividend", "needs_info" -> "Needs info"
export function humanize(value: string | null | undefined): string {
  if (!value) return "—";
  const text = value.toLowerCase().replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export type Tone = "amber" | "green" | "red" | "slate" | "sky";

export function analysisTone(status: string): Tone {
  if (status === "completed") return "green";
  if (status === "failed") return "red";
  if (status === "processing") return "sky";
  return "slate";
}

export function reviewTone(status: string): Tone {
  switch (status) {
    case "approved":
    case "reviewed":
      return "green";
    case "rejected":
    case "flagged":
      return "red";
    case "needs_info":
      return "sky";
    case "pending":
      return "amber";
    default:
      return "slate";
  }
}

export function severityTone(severity: string): Tone {
  if (severity === "high") return "red";
  if (severity === "medium") return "amber";
  return "slate";
}

export function stageTone(status: string): Tone {
  if (status === "completed") return "green";
  if (status === "failed") return "red";
  if (status === "running") return "sky";
  return "slate";
}
