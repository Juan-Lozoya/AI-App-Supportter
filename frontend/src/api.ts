const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export interface CreateAnalysisResponse {
  analysis_id: string;
  status: string;
  files: Files[];
}

interface Files {
  filename: string;
  role: string;
  sha256: string;
}

export async function createAnalysis(
  formData: FormData,
): Promise<CreateAnalysisResponse> {
  const response = await fetch(`${API_URL}/api/analyses`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let detail = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") detail = body.detail;
    } catch {
      /* la respuesta no era JSON */
    }
    throw new Error(detail);
  }

  return response.json();
}
