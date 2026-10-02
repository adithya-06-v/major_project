import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export interface PredictionRequest {
  sequence: string;
}

export interface ClinicalInsight {
  summary: string;
  biological_mechanism: string;
  pathogenicity_tier: string;
  clinical_recommendations: string[];
  confirmatory_tests: string[];
  hatchable_cloud_active: boolean;
  generated_at: string;
}

export interface PredictionResponse {
  prediction: string;
  confidence: number;
  sequence_length?: number;
  gc_content?: number;
  at_content?: number;
  model_used?: string;
  timestamp?: string;
  clinical_insight?: ClinicalInsight | null;
}

export interface HatchableStatus {
  status: string;
  connected: boolean;
  mcp_url: string;
  tools_available: number;
  masked_api_key?: string | null;
  error?: string | null;
  timestamp: string;
}

export const predictSequence = async (
  sequence: string
): Promise<PredictionResponse> => {
  try {
    const response = await axios.post<PredictionResponse>(
      `${API_BASE_URL}/predict`,
      { sequence }
    );
    return response.data;
  } catch (error: any) {
    if (axios.isAxiosError(error)) {
      if (error.response) {
        const detail = error.response.data?.detail;
        if (typeof detail === 'string') {
          throw new Error(detail);
        }
        throw new Error(`Server returned HTTP ${error.response.status}`);
      } else if (error.request) {
        throw new Error(
          'API service is currently unavailable. Please check backend server connection.'
        );
      }
    }
    throw new Error(error.message || 'An unexpected error occurred during prediction.');
  }
};

export const getHatchableStatus = async (): Promise<HatchableStatus> => {
  const response = await axios.get<HatchableStatus>(
    `${API_BASE_URL}/api/hatchable/status`
  );
  return response.data;
};
