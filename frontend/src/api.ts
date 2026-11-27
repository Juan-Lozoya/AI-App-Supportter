import axios from "axios";

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
  try {
    const { data } = await axios.post<CreateAnalysisResponse>(
      `${API_URL}/api/analyses`,
      formData,
    );

    return data;
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const detail = error.response?.data?.detail;

      throw new Error(
        typeof detail === "string"
          ? detail
          : `Request failed (${error.response?.status ?? "Network Error"})`,
        { cause: error },
      );
    }

    throw error;
  }
}
