import { useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import type { FormEvent } from "react";

import { useCreateAnalysis } from "../api/hooks";
import { ApiStatus } from "./ApiStatus";

const inputFile =
  "mt-2 w-full text-[13px] file:mr-3 file:rounded-md file:border-0 file:bg-brand-soft file:px-3 file:py-2 file:font-bold file:text-brand";

export function AnalysisForm() {
  const navigate = useNavigate();
  const create = useCreateAnalysis();
  const [files, setFiles] = useState<File[]>([]);
  const [pastedText, setPastedText] = useState("");
  const [holdingsFile, setHoldingsFile] = useState<File | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (files.length === 0 && !pastedText.trim()) {
      setFormError("Upload at least one document or paste announcement text.");
      return;
    }
    setFormError(null);
    create.mutate(
      { files, pastedText, holdingsFile },
      {
        onSuccess: (created) =>
          navigate({
            to: "/analyses/$analysisId",
            params: { analysisId: created.analysis_id },
          }),
      },
    );
  }

  const error = formError ?? create.error?.message;

  return (
    <form
      onSubmit={handleSubmit}
      className="rounded-xl border border-line bg-white p-6"
    >
      <h2 className="mb-2 text-lg font-bold">New Corporate Action Analysis</h2>
      <p className="mb-5 text-[13px] text-muted">
        Upload an announcement or paste the information below.
      </p>

      <div className="mb-5 rounded-[10px] border-2 border-dashed border-slate-300 bg-slate-50 p-6">
        <label className="block text-[13px] font-bold">
          Announcement documents
          <span className="mt-1 block font-normal text-muted">
            PDF, Excel, CSV or TXT files
          </span>
          <input
            type="file"
            multiple
            accept=".pdf,.xlsx,.xls,.csv,.txt"
            className={inputFile}
            onChange={(e) => setFiles(Array.from(e.target.files ?? []))}
          />
        </label>
        {files.length > 0 && (
          <p className="mt-2 text-xs text-muted">
            {files.map((f) => f.name).join(", ")}
          </p>
        )}
      </div>

      <label className="mb-5 block text-[13px] font-bold">
        Or paste the announcement text
        <textarea
          rows={8}
          value={pastedText}
          placeholder="Paste corporate action announcement details here..."
          onChange={(e) => setPastedText(e.target.value)}
          className="mt-2 min-h-36 w-full resize-y rounded-lg border border-slate-300 p-3 text-sm font-normal focus:border-transparent focus:outline-2 focus:outline-accent"
        />
      </label>

      <div className="mb-5 rounded-[10px] border-2 border-dashed border-slate-300 bg-slate-50 p-6">
        <label className="block text-[13px] font-bold">
          Portfolio holdings file (optional)
          <span className="mt-1 block font-normal text-muted">
            Excel or CSV file
          </span>
          <input
            type="file"
            accept=".xlsx,.xls,.csv"
            className={inputFile}
            onChange={(e) => setHoldingsFile(e.target.files?.[0] ?? null)}
          />
        </label>
      </div>

      <button
        type="submit"
        disabled={create.isPending}
        className="w-full rounded-lg bg-brand p-3.5 text-[15px] font-bold text-white hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
      >
        {create.isPending ? "Uploading…" : "Analyze corporate action"}
      </button>

      {create.isPending && (
        <ApiStatus state="loading" title="Uploading files">
          The analysis starts as soon as the upload finishes.
        </ApiStatus>
      )}
      {error && (
        <ApiStatus state="error" title="Could not start the analysis">
          {error}
        </ApiStatus>
      )}
    </form>
  );
}
