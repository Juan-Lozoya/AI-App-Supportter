export type ApiState =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "success"; analysisId: string; files: string[]; status: string }
  | { kind: "error"; message: string };

export default function ApiStatus({ state }: { state: ApiState }) {
  if (state.kind === "idle") return null;

  return (
    <div className={`api-status ${state.kind}`} aria-live="polite">
      {state.kind === "loading" && <strong>Uploading documents...</strong>}

      {state.kind === "error" && (
        <>
          <strong>Error</strong>
          {state.message}
        </>
      )}

      {state.kind === "success" && (
        <>
          <strong>Documents received</strong>
          Analysis ID: {state.analysisId}
          <br />
          Status: {state.status}
          <br />
          Files: {state.files.join(", ")}
          <br />
          <em>AI analysis is not implemented yet.</em>
        </>
      )}
    </div>
  );
}
