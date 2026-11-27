import type { components } from "./schema";

// Alias cortos de los tipos generados desde el backend (src/api/schema.d.ts).
type Schemas = components["schemas"];

export type AnalysisCreated = Schemas["AnalysisCreated"];
export type AnalysisDetail = Schemas["AnalysisDetail"];
export type AnalysisList = Schemas["AnalysisList"];
export type AnalysisSummary = Schemas["AnalysisSummary"];
export type AnalysisStatus = Schemas["AnalysisSummary"]["status"];
export type DashboardStats = Schemas["DashboardStats"];
export type OverviewResponse = Schemas["OverviewResponse"];
export type KeyDatesResponse = Schemas["KeyDatesResponse"];
export type HoldingsResponse = Schemas["HoldingsResponse"];
export type HoldingMatch = Schemas["HoldingMatch"];
export type AlertsResponse = Schemas["AlertsResponse"];
export type Alert = Schemas["Alert"];
export type ProcessingResponse = Schemas["ProcessingResponse"];
export type StageRecord = Schemas["StageRecord"];
export type ReviewRequest = Schemas["ReviewRequest"];
export type ReviewResponse = Schemas["ReviewResponse"];
export type HoldingReviewRequest = Schemas["HoldingReviewRequest"];
export type DocumentsResponse = Schemas["DocumentsResponse"];
export type EventTypeOption = Schemas["EventTypeOption"];

export interface ListParams {
  status?: AnalysisStatus;
  review_status?: ReviewRequest["decision"] | "pending";
  event_type?: string;
  q?: string;
  limit?: number;
  offset?: number;
}

export interface CreateAnalysisInput {
  files: File[];
  pastedText: string;
  holdingsFile: File | null;
}
