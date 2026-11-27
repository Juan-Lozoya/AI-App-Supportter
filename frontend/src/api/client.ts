import type {
  AlertsResponse,
  AnalysisCreated,
  AnalysisDetail,
  AnalysisList,
  CreateAnalysisInput,
  DashboardStats,
  DocumentsResponse,
  EventTypeOption,
  HoldingMatch,
  HoldingReviewRequest,
  HoldingsResponse,
  KeyDatesResponse,
  ListParams,
  OverviewResponse,
  ProcessingResponse,
  ReviewRequest,
  ReviewResponse,
} from "./types";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

// FastAPI devuelve { detail: string } o { detail: [{ msg }] } según el tipo de error.
function errorMessage(body: unknown, status: number): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      const messages = detail
        .map((item) =>
          typeof item === "object" && item !== null && "msg" in item
            ? String(item.msg)
            : "",
        )
        .filter(Boolean);
      if (messages.length) return messages.join("; ");
    }
  }
  return `Request failed (${status}).`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api${path}`, init);
  } catch {
    throw new ApiError(
      0,
      "Cannot reach the server. Check that the backend is running.",
    );
  }

  if (!response.ok) {
    let body: unknown = null;
    try {
      body = await response.json();
    } catch {
      // la respuesta de error no era JSON
    }
    throw new ApiError(response.status, errorMessage(body, response.status));
  }
  return (await response.json()) as T;
}

function jsonBody(method: string, payload: unknown): RequestInit {
  return {
    method,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
}

function queryString(params: ListParams): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") search.set(key, String(value));
  }
  const text = search.toString();
  return text ? `?${text}` : "";
}

export const api = {
  dashboardStats: () => request<DashboardStats>("/dashboard/stats"),
  eventTypes: () => request<EventTypeOption[]>("/meta/event-types"),
  listAnalyses: (params: ListParams = {}) =>
    request<AnalysisList>(`/analyses${queryString(params)}`),

  createAnalysis: (input: CreateAnalysisInput) => {
    // No se fija Content-Type: el navegador agrega el boundary del multipart.
    const form = new FormData();
    input.files.forEach((file) => form.append("files", file));
    if (input.pastedText.trim()) form.append("pasted_text", input.pastedText);
    if (input.holdingsFile) form.append("holdings_file", input.holdingsFile);
    return request<AnalysisCreated>("/analyses", {
      method: "POST",
      body: form,
    });
  },
  retryAnalysis: (id: string) =>
    request<AnalysisCreated>(`/analyses/${id}/retry`, { method: "POST" }),

  getAnalysis: (id: string) => request<AnalysisDetail>(`/analyses/${id}`),
  overview: (id: string) =>
    request<OverviewResponse>(`/analyses/${id}/overview`),
  keyDates: (id: string) => request<KeyDatesResponse>(`/analyses/${id}/dates`),
  holdings: (id: string) =>
    request<HoldingsResponse>(`/analyses/${id}/holdings`),
  alerts: (id: string) => request<AlertsResponse>(`/analyses/${id}/alerts`),
  processing: (id: string) =>
    request<ProcessingResponse>(`/analyses/${id}/processing`),
  documents: (id: string) =>
    request<DocumentsResponse>(`/analyses/${id}/documents`),

  getReview: (id: string) => request<ReviewResponse>(`/analyses/${id}/review`),
  submitReview: (id: string, body: ReviewRequest) =>
    request<ReviewResponse>(`/analyses/${id}/review`, jsonBody("POST", body)),
  updateHolding: (id: string, matchId: string, body: HoldingReviewRequest) =>
    request<HoldingMatch>(
      `/analyses/${id}/holdings/${matchId}`,
      jsonBody("PATCH", body),
    ),
};
