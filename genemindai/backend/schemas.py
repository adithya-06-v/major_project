"""
Pydantic schemas for API request and response validation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PredictionRequest(BaseModel):
    """DNA sequence prediction request payload."""

    sequence: str = Field(
        ...,
        description="Raw DNA nucleotide sequence string (A, T, C, G).",
        examples=["ACATTTGCTTCTGACACAACTGTGTTCACTAGCAACCTCAAACAGACACCATGGTGCAT"],
    )


class TestSampleResponse(BaseModel):
    sequence: str
    label: str
    source_notice: str


class ClinicalInsight(BaseModel):
    """Structured AI clinical genomic advisory interpretation."""

    summary: str = Field(
        ...,
        description="Executive clinical summary of the diagnostic finding.",
    )
    biological_mechanism: str = Field(
        ...,
        description="Molecular impact on the beta-globin polypeptide chain.",
    )
    pathogenicity_tier: str = Field(
        ...,
        description="Clinical classification tier according to ACMG/AMP guidelines.",
    )
    clinical_recommendations: List[str] = Field(
        default_factory=list,
        description="Recommended clinical next steps and counseling guidance.",
    )
    confirmatory_tests: List[str] = Field(
        default_factory=list,
        description="Recommended secondary laboratory diagnostic assays.",
    )
    hatchable_cloud_active: bool = Field(
        False,
        description="Indicates whether the Hatchable cloud MCP connection was active.",
    )
    generated_at: str = Field(
        ...,
        description="Formatted timestamp of clinical interpretation synthesis.",
    )


class PredictionResponse(BaseModel):
    """DNA sequence prediction response payload."""

    prediction: str = Field(
        ...,
        description="Predicted sequence classification label (Healthy or Beta Thalassemia).",
        examples=["Healthy"],
    )
    confidence: float = Field(
        ...,
        description="Model prediction confidence score between 0.0 and 1.0.",
        examples=[0.71],
    )
    sequence_length: Optional[int] = Field(
        None,
        description="Sequence length in base pairs.",
        examples=[1606],
    )
    gc_content: Optional[float] = Field(
        None,
        description="GC content percentage.",
        examples=[52.3],
    )
    at_content: Optional[float] = Field(
        None,
        description="AT content percentage.",
        examples=[47.7],
    )
    model_used: Optional[str] = Field(
        "Random Forest",
        description="Machine learning model used for inference.",
        examples=["Random Forest"],
    )
    supported_classes: List[str] = Field(
        default_factory=list,
        description="Class labels supported by the loaded model.",
    )
    training_data_notice: Optional[str] = Field(
        None,
        description="Limitations and intended use of the loaded model.",
    )
    timestamp: Optional[str] = Field(
        None,
        description="Timestamp of prediction execution.",
        examples=["July 30, 2026 at 22:30:52"],
    )
    clinical_insight: Optional[ClinicalInsight] = Field(
        None,
        description="Server-side AI clinical interpretation powered by Hatchable integration.",
    )


class ClinicalInsightRequest(BaseModel):
    """Request payload to query standalone clinical genomic interpretation."""

    prediction: str = Field(
        ...,
        description="Classification label ('Healthy' or 'Beta Thalassemia').",
        examples=["Beta Thalassemia"],
    )
    confidence: float = Field(
        ...,
        description="Prediction confidence (0.0 to 1.0).",
        examples=[0.96],
    )
    sequence_length: int = Field(
        ...,
        description="Length of sequence in base pairs.",
        examples=[1608],
    )
    gc_content: Optional[float] = Field(
        None,
        description="GC content percentage.",
        examples=[40.11],
    )
    at_content: Optional[float] = Field(
        None,
        description="AT content percentage.",
        examples=[59.89],
    )


class HatchableStatusResponse(BaseModel):
    """Server-side status of Hatchable MCP integration (no secret keys exposed)."""

    status: str = Field(..., description="Connection status ('online', 'unconfigured', etc.)")
    connected: bool = Field(..., description="True if server-side handshake succeeded")
    mcp_url: str = Field(..., description="Target MCP endpoint URL")
    tools_available: int = Field(..., description="Count of available MCP tools")
    masked_api_key: Optional[str] = Field(
        None,
        description="Safely masked API key prefix/suffix (e.g. hb_SST...AbjaD)",
    )
    error: Optional[str] = Field(None, description="Error detail if connection failed")
    timestamp: str = Field(..., description="ISO timestamp of status check")
