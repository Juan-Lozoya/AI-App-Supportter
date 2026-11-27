import { createFileRoute } from "@tanstack/react-router";

import { AnalysisForm } from "../components/AnalysisForm";
import { Header } from "../components/Header";

export const Route = createFileRoute("/analyses/new")({
  component: NewAnalysis,
});

function NewAnalysis() {
  return (
    <>
      <Header
        title="New Analysis"
        subtitle="Upload an announcement or paste its text to extract the corporate action."
      />
      <div className="max-w-3xl">
        <AnalysisForm />
      </div>
    </>
  );
}
