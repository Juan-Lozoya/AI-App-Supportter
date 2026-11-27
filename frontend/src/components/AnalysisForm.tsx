import { useState, type ChangeEvent, type FormEvent } from "react";
import { createAnalysis } from "../api";
import ApiStatus, { type ApiState } from "./ApiStatus";

const ALLOWED = [".pdf", ".xlsx", ".xls", ".csv", ".txt"];

function hasAllowedExtension(file: File): boolean {
  const name = file.name.toLowerCase();
  return ALLOWED.some((ext) => name.endsWith(ext));
}

export default function AnalysisForm() {
  const [files, setFiles] = useState<File[]>([]);
  const [pastedText, setPastedText] = useState("");
  const [holdingsFile, setHoldingsFile] = useState<File | null>(null);
  const [state, setState] = useState<ApiState>({ kind: "idle" });

  const isLoading = state.kind === "loading";

  const handleFiles = (e: ChangeEvent<HTMLInputElement>) =>
    setFiles(Array.from(e.target.files ?? []));

  const handleHoldings = (e: ChangeEvent<HTMLInputElement>) =>
    setHoldingsFile(e.target.files?.[0] ?? null);

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const text = pastedText.trim();
    if (files.length === 0 && !text) {
      setState({
        kind: "error",
        message: "Upload at least one file or paste announcement text.",
      });
      return;
    }

    const invalid = [...files, ...(holdingsFile ? [holdingsFile] : [])].find(
      (f) => !hasAllowedExtension(f),
    );
    if (invalid) {
      setState({
        kind: "error",
        message: `File format not supported: ${invalid.name}`,
      });
      return;
    }

    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    if (text) formData.append("pasted_text", text);
    if (holdingsFile) formData.append("holdings_file", holdingsFile);

    setState({ kind: "loading" });
    try {
      const result = await createAnalysis(formData);

      setState({
        kind: "success",
        analysisId: result.analysis_id,
        files: result.files.map((f) => f.filename),
        status: result.status,
      });
    } catch (err) {
      setState({
        kind: "error",
        message:
          err instanceof TypeError
            ? "Could not reach the backend. Is it running on port 8000?"
            : (err as Error).message,
      });
    }
  };

  return (
    <div className="panel">
      <h2>New Corporate Action Analysis</h2>
      <p className="panel-description">
        Upload an announcement or paste the information below.
      </p>

      <form onSubmit={handleSubmit}>
        <label htmlFor="files">Corporate Action Documents</label>
        <div className="upload-box">
          <strong>Upload announcement files</strong>
          <p>PDF, Excel, CSV or TXT files</p>
          <input
            id="files"
            type="file"
            accept={ALLOWED.join(",")}
            multiple
            onChange={handleFiles}
          />
        </div>

        <label htmlFor="pasted_text">Paste Announcement Text</label>
        <textarea
          id="pasted_text"
          value={pastedText}
          onChange={(e) => setPastedText(e.target.value)}
          placeholder="Paste corporate action announcement details here..."
        />

        <label htmlFor="holdings_file">
          Portfolio Holdings File (Optional)
        </label>
        <div className="upload-box">
          <strong>Upload portfolio / holdings</strong>
          <p>Excel or CSV file</p>
          <input
            id="holdings_file"
            type="file"
            accept=".xlsx,.xls,.csv"
            onChange={handleHoldings}
          />
        </div>

        <button type="submit" className="button" disabled={isLoading}>
          {isLoading ? "Uploading..." : "Analyze Corporate Action"}
        </button>
      </form>

      <ApiStatus state={state} />
    </div>
  );
}
