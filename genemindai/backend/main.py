"""
FastAPI REST API server for GeneMindAI DNA sequence mutation analysis.

Exposes endpoints to health check the service, run real-time sequence prediction,
and access server-side Hatchable AI clinical genomic insights.
"""

from __future__ import annotations

import csv
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from random import choice
from typing import Dict, Literal, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.schemas import (
    ClinicalInsight,
    ClinicalInsightRequest,
    HatchableStatusResponse,
    PredictionRequest,
    PredictionResponse,
    TestSampleResponse,
)
from backend.services.hatchable_service import HatchableService
from backend.services.predictor import (
    InvalidDNASequenceError,
    Predictor,
    PredictorError,
)

# Global services initialized during application startup
predictor_service: Optional[Predictor] = None
hatchable_service: Optional[HatchableService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager to load models and services once at startup."""
    global predictor_service, hatchable_service
    try:
        predictor_service = Predictor()
    except Exception as exc:
        print(f"Error initializing predictor service: {exc}", file=sys.stderr)
        predictor_service = None

    try:
        hatchable_service = HatchableService()
    except Exception as exc:
        print(f"Error initializing hatchable service: {exc}", file=sys.stderr)
        hatchable_service = None

    yield
    predictor_service = None
    hatchable_service = None


app = FastAPI(
    title="GeneMindAI API",
    description="DNA Sequence Mutation Analysis & Beta Thalassemia Prediction API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

reports_dir = PROJECT_ROOT / "reports"
DISEASE_TEST_FOLDERS = {
    "beta_thalassemia": "Beta Thalassemia",
    "sickle_cell_disease": "Sickle Cell Disease",
    "hemoglobin_e": "Hemoglobin E Disease",
    "hemoglobin_c_disease": "Hemoglobin C Disease",
}
if reports_dir.is_dir():
    app.mount("/reports", StaticFiles(directory=reports_dir), name="reports")


@app.get("/", status_code=status.HTTP_200_OK)
async def root() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        JSON response with API status message.
    """
    return {"message": "GeneMindAI API Running"}


@app.get("/api/test-sample", response_model=TestSampleResponse)
async def get_test_sample(
    kind: Literal["healthy", "disease"] = "healthy",
) -> TestSampleResponse:
    """Return a Healthy fixture or a random disease fixture for the demo UI."""
    if kind == "healthy":
        dataset_path = PROJECT_ROOT / "dataset" / "processed" / "expanded_dataset.csv"
        label = "Healthy"
        with dataset_path.open(encoding="utf-8", newline="") as stream:
            rows = [row for row in csv.DictReader(stream) if row.get("label") == "0"]
    else:
        folder, label = choice(list(DISEASE_TEST_FOLDERS.items()))
        dataset_path = (
            PROJECT_ROOT
            / "dataset"
            / "diseases"
            / folder
            / "sample_test_dataset.csv"
        )
        with dataset_path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))

    if not rows:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"No {label} test samples are available.",
        )

    return TestSampleResponse(
        sequence=choice(rows)["sequence"],
        label=label,
        source_notice="Synthetic test fixture; not validated clinical data.",
    )


@app.get(
    "/api/hatchable/status",
    response_model=HatchableStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_hatchable_status() -> HatchableStatusResponse:
    """
    Check the server-side Hatchable MCP connection status.

    Returns:
        HatchableStatusResponse with connection health and available cloud tools,
        without ever exposing the secret API key.
    """
    if hatchable_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hatchable service is not initialized.",
        )

    status_data = await hatchable_service.check_connection()
    return HatchableStatusResponse(**status_data)


@app.post(
    "/api/hatchable/clinical-insight",
    response_model=ClinicalInsight,
    status_code=status.HTTP_200_OK,
)
async def get_clinical_insight(
    request: ClinicalInsightRequest,
) -> ClinicalInsight:
    """
    Generate an AI clinical genomic advisory interpretation for a given classification result.

    Args:
        request: ClinicalInsightRequest containing prediction, confidence, and sequence metrics.

    Returns:
        ClinicalInsight response.
    """
    if hatchable_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Hatchable service is not initialized.",
        )

    insight_dict = await hatchable_service.generate_clinical_insight(
        prediction=request.prediction,
        confidence=request.confidence,
        sequence_length=request.sequence_length,
        gc_content=request.gc_content,
        at_content=request.at_content,
    )
    return ClinicalInsight(**insight_dict)


@app.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
)
async def predict_dna_sequence(
    request: PredictionRequest,
) -> PredictionResponse:
    """
    Predict mutation status for a given DNA sequence and augment with clinical insight.

    Args:
        request: PredictionRequest containing the DNA sequence.

    Returns:
        PredictionResponse containing classification label, confidence score,
        sequence metrics, and server-side Hatchable AI clinical insights.

    Raises:
        HTTPException 400: If the DNA sequence is invalid.
        HTTPException 500: If predictor is unavailable or inference fails.
    """
    if predictor_service is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Predictor service is not initialized.",
        )

    try:
        result_dict = dict(predictor_service.predict(request.sequence))
    except InvalidDNASequenceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PredictorError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    # Enforce server-side AI Clinical Insight enrichment
    if hatchable_service is not None and len(predictor_service.class_labels) <= 2:
        try:
            insight_dict = await hatchable_service.generate_clinical_insight(
                prediction=result_dict.get("prediction", ""),
                confidence=float(result_dict.get("confidence", 0.0)),
                sequence_length=int(result_dict.get("sequence_length", 0)),
                gc_content=result_dict.get("gc_content"),
                at_content=result_dict.get("at_content"),
            )
            result_dict["clinical_insight"] = insight_dict
        except Exception as exc:
            print(f"Warning: Failed to generate clinical insight: {exc}", file=sys.stderr)
            result_dict["clinical_insight"] = None

    return PredictionResponse(**result_dict)
