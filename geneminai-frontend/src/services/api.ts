import axios, { AxiosError } from "axios";

export const API_BASE_URL =
  import.meta.env["VITE_API_BASE_URL"] || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30_000,
  headers: { "Content-Type": "application/json" },
});

export type Prediction = string;

export interface AnalysisResponse {
  prediction: Prediction | null;
  confidence: number | null;
  sequence_length: number | null;
  gc_content: number | null;
  at_content: number | null;
  model_used: string | null;
  supported_classes?: string[];
  training_data_notice?: string | null;
  timestamp: string | null;
  clinical_insight?: string | null;
  hatchable_cloud_active?: boolean | null;
  generated_at?: string | null;
}

export interface TestSample {
  sequence: string;
  label: string;
  source_notice: string;
}

function nullableNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function nullableString(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function normalizeAnalysisResponse(data: unknown): AnalysisResponse {
  const response = typeof data === "object" && data !== null
    ? data as Record<string, unknown>
    : {};
  const prediction = response["prediction"];

  return {
    prediction: nullableString(prediction),
    confidence: nullableNumber(response["confidence"]),
    sequence_length: nullableNumber(response["sequence_length"]),
    gc_content: nullableNumber(response["gc_content"]),
    at_content: nullableNumber(response["at_content"]),
    model_used: nullableString(response["model_used"]),
    supported_classes: Array.isArray(response["supported_classes"])
      ? response["supported_classes"].filter((label): label is string => typeof label === "string")
      : [],
    training_data_notice: nullableString(response["training_data_notice"]),
    timestamp: nullableString(response["timestamp"]),
    clinical_insight: nullableString(response["clinical_insight"]),
    hatchable_cloud_active: typeof response["hatchable_cloud_active"] === "boolean"
      ? response["hatchable_cloud_active"]
      : null,
    generated_at: nullableString(response["generated_at"]),
  };
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await api.get<{ message?: string }>("/");
    return response.status === 200;
  } catch {
    return false;
  }
}

export async function analyzeSequence(sequence: string): Promise<AnalysisResponse> {
  const response = await api.post<unknown>("/predict", { sequence });
  return normalizeAnalysisResponse(response.data);
}

export async function getTestSample(kind: "healthy" | "disease"): Promise<TestSample> {
  const response = await api.get<TestSample>("/api/test-sample", { params: { kind } });
  return response.data;
}

export function getApiErrorMessage(error: unknown): string {
  if (!(error instanceof AxiosError)) {
    return "The analysis could not be completed. Please try again.";
  }

  if (!error.response) {
    return "The GeneMindAI backend is offline. Start the API and try again.";
  }

  const detail = (error.response.data as { detail?: unknown } | undefined)?.detail;
  if (error.response.status === 400 && typeof detail === "string") return detail;
  if (error.response.status >= 500) {
    if (detail === "Predictor service is not initialized.") {
      return "The API is online, but its prediction model failed to load. Check the backend terminal startup error, resolve it, and restart the API before analyzing sequences.";
    }
    return "The backend encountered an error while analyzing this sequence.";
  }
  return "The sequence could not be analyzed. Please review the input and try again.";
}
