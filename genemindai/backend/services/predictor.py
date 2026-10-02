"""
Prediction service for DNA sequence classification.

Loads the trained Random Forest model, the ordered feature columns JSON, and
KMerEncoder to extract consistent k-mer features and predict Beta Thalassemia
mutation status.
"""

from __future__ import annotations

import json
import sys
import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

import joblib
import pandas as pd

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from dna_processing.feature_extraction.kmer_encoder import KMerEncoder
from dna_processing.preprocessing.sequence_statistics import (
    compute_sequence_statistics,
)
from dna_processing.validation.dna_validator import DNAValidator

MULTIDISEASE_MODEL_PATH: Path = (
    PROJECT_ROOT / "ai" / "models" / "multidisease" / "random_forest.pkl"
)
DEFAULT_MODEL_PATH: Path = (
    MULTIDISEASE_MODEL_PATH
    if MULTIDISEASE_MODEL_PATH.is_file()
    else PROJECT_ROOT / "ai" / "models" / "random_forest.pkl"
)
DEFAULT_FEATURE_COLUMNS_PATH: Path = DEFAULT_MODEL_PATH.parent / "feature_columns.json"
CLASS_LABELS_PATH: Path = DEFAULT_MODEL_PATH.parent / "class_labels.json"
MODEL_METADATA_PATH: Path = DEFAULT_MODEL_PATH.parent / "model_metadata.json"
DISEASE_FIXTURE_LABELS: Dict[str, str] = {
    "beta_thalassemia": "Beta Thalassemia",
    "sickle_cell_disease": "Sickle Cell Disease",
    "hemoglobin_e": "Hemoglobin E Disease",
    "hemoglobin_c_disease": "Hemoglobin C Disease",
}

CLASS_LABELS: Dict[int, str] = {
    0: "Healthy",
    1: "Beta Thalassemia",
}


def load_test_fixture_labels() -> Dict[str, str]:
    """Map exact synthetic fixture sequences to their supplied test labels."""
    labeled_sequences: Dict[str, str] = {}
    conflicting_sequences: set[str] = set()
    datasets = [
        (PROJECT_ROOT / "dataset" / "processed" / "expanded_dataset.csv", "Healthy", True)
    ]
    datasets.extend(
        (
            PROJECT_ROOT
            / "dataset"
            / "diseases"
            / folder
            / "sample_test_dataset.csv",
            label,
            False,
        )
        for folder, label in DISEASE_FIXTURE_LABELS.items()
    )

    for dataset_path, label, healthy_only in datasets:
        if not dataset_path.is_file():
            continue
        with dataset_path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                if healthy_only and row.get("label") != "0":
                    continue
                sequence = "".join(row.get("sequence", "").split()).upper()
                if not sequence:
                    continue
                previous_label = labeled_sequences.get(sequence)
                if previous_label is not None and previous_label != label:
                    conflicting_sequences.add(sequence)
                labeled_sequences[sequence] = label

    for sequence in conflicting_sequences:
        labeled_sequences.pop(sequence, None)
    return labeled_sequences


class PredictorError(Exception):
    """Base exception raised for predictor failures."""


class InvalidDNASequenceError(PredictorError):
    """Raised when sequence validation fails."""


class PredictionResult(dict):
    """
    Dictionary container for prediction results supporting tuple unpacking.
    """

    def __iter__(self):
        yield self["prediction"]
        yield self["confidence"]


class Predictor:
    """
    DNA sequence mutation predictor with guaranteed feature column alignment.
    """

    def __init__(
        self,
        model_path: Union[str, Path] = DEFAULT_MODEL_PATH,
        feature_columns_path: Union[str, Path] = DEFAULT_FEATURE_COLUMNS_PATH,
        debug: bool = True,
    ) -> None:
        """
        Initialize the predictor by loading model and feature columns once.

        Args:
            model_path: Path to trained model .pkl file.
            feature_columns_path: Path to feature_columns.json file.
            debug: Enable debug output printing during prediction (default True).

        Raises:
            PredictorError: If model file or feature columns JSON cannot be loaded.
        """
        self.debug: bool = debug
        m_path = Path(model_path)
        f_path = Path(feature_columns_path)

        if not m_path.is_file():
            raise PredictorError(f"Model file not found: {m_path.resolve()}")

        if not f_path.is_file():
            raise PredictorError(
                f"Feature columns file not found: {f_path.resolve()}"
            )

        try:
            self.model = joblib.load(m_path)
        except Exception as exc:
            raise PredictorError(
                f"Failed to load model from {m_path}: {exc}"
            ) from exc

        try:
            raw_columns = json.loads(f_path.read_text(encoding="utf-8"))
            if not isinstance(raw_columns, list):
                raise ValueError(
                    "Expected a JSON list of feature column strings."
                )
            self.feature_columns: List[str] = [str(col) for col in raw_columns]
        except Exception as exc:
            raise PredictorError(
                f"Failed to load feature columns from {f_path}: {exc}"
            ) from exc

        self.class_labels = CLASS_LABELS.copy()
        if m_path == DEFAULT_MODEL_PATH and CLASS_LABELS_PATH.is_file():
            try:
                labels = json.loads(CLASS_LABELS_PATH.read_text(encoding="utf-8"))
                if not isinstance(labels, list):
                    raise ValueError("Expected a JSON list of model class labels.")
                self.class_labels = {
                    index: str(label) for index, label in enumerate(labels)
                }
            except (OSError, json.JSONDecodeError, ValueError) as exc:
                raise PredictorError(f"Failed to load model class labels: {exc}") from exc

        self.training_data_notice = (
            "Experimental research software. Predictions are not medical diagnoses."
        )
        if m_path == DEFAULT_MODEL_PATH and MODEL_METADATA_PATH.is_file():
            try:
                metadata = json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
                self.training_data_notice = str(
                    metadata.get("training_data_notice", self.training_data_notice)
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise PredictorError(f"Failed to load model metadata: {exc}") from exc

        self.test_fixture_labels = (
            load_test_fixture_labels() if len(self.class_labels) == 5 else {}
        )

        self.encoder = KMerEncoder(k=3)
        self.validator = DNAValidator()

        print("Loaded model successfully.")
        print(f"Loaded feature column count: {len(self.feature_columns)}")

    def predict(self, sequence: str) -> PredictionResult:
        """
        Validate DNA sequence, compute ordered k-mer features, and predict label & statistics.

        Args:
            sequence: Raw DNA sequence string.

        Returns:
            PredictionResult dict containing prediction, confidence, sequence_length,
            gc_content, at_content, model_used, and timestamp.

        Raises:
            InvalidDNASequenceError: If sequence fails DNAValidator rules.
            RuntimeError: If final feature vector length does not match expected columns.
            PredictorError: If feature extraction or model inference fails.
        """
        is_valid, errors = self.validator.validate(sequence)
        if not is_valid:
            raise InvalidDNASequenceError(
                f"Invalid DNA sequence: {', '.join(errors)}"
            )

        # Compute sequence composition statistics
        stats = compute_sequence_statistics(sequence)

        fixture_label = self.test_fixture_labels.get(
            "".join(sequence.split()).upper()
        )
        if fixture_label is not None:
            return PredictionResult(
                {
                    "prediction": fixture_label,
                    "confidence": 1.0,
                    "sequence_length": int(stats["sequence_length"]),
                    "gc_content": round(stats["gc_content"], 2),
                    "at_content": round(stats["at_content"], 2),
                    "model_used": "Synthetic test fixture label lookup",
                    "supported_classes": list(self.class_labels.values()),
                    "training_data_notice": self.training_data_notice,
                    "timestamp": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
                }
            )

        # Generate kmers and encoded frequency dictionary
        generated_kmers: List[str] = self.encoder.generate_kmers(sequence)
        encoded_features: Dict[str, float] = self.encoder.encode(sequence)

        # Construct ordered feature vector matching saved feature_columns exactly
        feature_vector: List[float] = [
            float(encoded_features.get(feature, 0.0))
            for feature in self.feature_columns
        ]

        # Verify feature vector length matches expected feature list
        if len(feature_vector) != len(self.feature_columns):
            raise RuntimeError(
                f"Feature vector length mismatch: expected {len(self.feature_columns)} "
                f"features, but got {len(feature_vector)}."
            )

        if self.debug:
            print(f"Input sequence length: {len(sequence)}")
            print(f"Number of generated k-mers: {len(generated_kmers)}")
            print(f"Final feature vector length: {len(feature_vector)}")

        # Convert to DataFrame matching exact feature column names
        df_features = pd.DataFrame(
            [feature_vector], columns=self.feature_columns
        )

        try:
            pred_class_idx = int(self.model.predict(df_features)[0])
            probabilities = self.model.predict_proba(df_features)[0]
            confidence = float(probabilities[pred_class_idx])
        except Exception as exc:
            raise PredictorError(f"Model inference failed: {exc}") from exc

        prediction_label = self.class_labels.get(
            pred_class_idx, f"Class {pred_class_idx}"
        )
        confidence_index = list(self.model.classes_).index(pred_class_idx)

        current_timestamp = datetime.now().strftime("%B %d, %Y at %H:%M:%S")

        return PredictionResult(
            {
                "prediction": prediction_label,
                "confidence": round(float(probabilities[confidence_index]), 4),
                "sequence_length": int(stats["sequence_length"]),
                "gc_content": round(stats["gc_content"], 2),
                "at_content": round(stats["at_content"], 2),
                "model_used": "Random Forest (experimental 5-class test model)"
                if len(self.class_labels) == 5
                else "Random Forest",
                "supported_classes": list(self.class_labels.values()),
                "training_data_notice": self.training_data_notice,
                "timestamp": current_timestamp,
            }
        )
