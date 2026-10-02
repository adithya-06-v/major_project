#!/usr/bin/env python3
"""Train an experimental multiclass model from disease-specific sequence CSVs."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import joblib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DISEASES_DIR = PROJECT_ROOT / "dataset" / "diseases"
BASELINE_DATASET_PATH = PROJECT_ROOT / "dataset" / "processed" / "expanded_dataset.csv"
MODEL_DIR = PROJECT_ROOT / "ai" / "models" / "multidisease"
DISEASE_LABELS: Dict[str, str] = {
    "beta_thalassemia": "Beta Thalassemia",
    "sickle_cell_disease": "Sickle Cell Disease",
    "hemoglobin_e": "Hemoglobin E Disease",
    "hemoglobin_c_disease": "Hemoglobin C Disease",
}


class MultidiseaseTrainingError(Exception):
    """Raised when disease-specific training data is invalid or incomplete."""


def load_sequences(data_dir: Path) -> Tuple[List[str], List[str], List[str]]:
    """Load synthetic Healthy controls and one labeled CSV per disease."""
    sequences: List[str] = []
    labels: List[str] = []
    sources: List[str] = []

    if not BASELINE_DATASET_PATH.is_file():
        raise MultidiseaseTrainingError(
            f"Healthy/control samples not found: {BASELINE_DATASET_PATH}"
        )
    with BASELINE_DATASET_PATH.open(encoding="utf-8", newline="") as stream:
        healthy_rows = [
            row for row in csv.DictReader(stream) if row.get("label") == "0"
        ]
    if len(healthy_rows) < 2:
        raise MultidiseaseTrainingError(
            "At least two Healthy/control samples are required."
        )

    for row in healthy_rows:
        sequence = re.sub(r"\s+", "", row.get("sequence", "")).upper()
        if not sequence or re.search(r"[^ATCGN]", sequence):
            raise MultidiseaseTrainingError(
                f"Invalid Healthy/control DNA sequence (sample {row.get('id', 'unknown')})."
            )
        sequences.append(sequence)
        labels.append("Healthy")
        sources.append("synthetic_test")

    for folder_name, display_label in DISEASE_LABELS.items():
        dataset_path = data_dir / folder_name / "sample_test_dataset.csv"
        if not dataset_path.is_file():
            raise MultidiseaseTrainingError(f"Dataset not found: {dataset_path}")

        with dataset_path.open(encoding="utf-8", newline="") as stream:
            rows = list(csv.DictReader(stream))
        if len(rows) < 2:
            raise MultidiseaseTrainingError(
                f"At least two samples are required for {display_label}."
            )

        for row in rows:
            sequence = re.sub(r"\s+", "", row.get("sequence", "")).upper()
            if not sequence or re.search(r"[^ATCGN]", sequence):
                raise MultidiseaseTrainingError(
                    f"Invalid DNA sequence in {dataset_path} (sample {row.get('id', 'unknown')})."
                )
            if row.get("label") != folder_name:
                raise MultidiseaseTrainingError(
                    f"Label mismatch in {dataset_path}: expected {folder_name!r}."
                )
            sequences.append(sequence)
            labels.append(display_label)
            sources.append(row.get("source", "unspecified"))

    return sequences, labels, sources


def train_model(
    data_dir: Path = DISEASES_DIR,
    model_dir: Path = MODEL_DIR,
    allow_synthetic_test_data: bool = False,
) -> Dict[str, object]:
    """Train and serialize a multiclass model, requiring explicit synthetic-data consent."""
    sequences, labels, sources = load_sequences(data_dir)
    if "synthetic_test" in sources and not allow_synthetic_test_data:
        raise MultidiseaseTrainingError(
            "Synthetic test data is present. Pass --allow-synthetic-test-data to "
            "train a demonstration model; its predictions are not clinically valid."
        )

    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import classification_report
    from sklearn.model_selection import train_test_split

    import pandas as pd

    encoder_classes = sorted(set(labels))
    label_to_id = {label: index for index, label in enumerate(encoder_classes)}
    encoded_labels = [label_to_id[label] for label in labels]
    class_counts = Counter(encoded_labels)
    if any(count < 2 for count in class_counts.values()):
        raise MultidiseaseTrainingError(
            "Each disease class must contain at least two samples."
        )

    feature_columns = [
        first + second + third
        for first in "ACGT"
        for second in "ACGT"
        for third in "ACGT"
    ]
    feature_rows = []
    for sequence in sequences:
        total = max(1, len(sequence) - 2)
        counts = {feature: 0 for feature in feature_columns}
        for index in range(total):
            kmer = sequence[index : index + 3]
            if kmer in counts:
                counts[kmer] += 1
        feature_rows.append({key: value / total for key, value in counts.items()})
    features = pd.DataFrame(feature_rows, columns=feature_columns)

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        encoded_labels,
        test_size=0.2,
        random_state=42,
        stratify=encoded_labels,
    )
    model = RandomForestClassifier(
        n_estimators=200,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)

    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, model_dir / "random_forest.pkl")
    (model_dir / "feature_columns.json").write_text(
        json.dumps(feature_columns, indent=2), encoding="utf-8"
    )
    (model_dir / "class_labels.json").write_text(
        json.dumps(encoder_classes, indent=2), encoding="utf-8"
    )
    notice = (
        "Experimental test model trained with synthetic examples. Predictions are "
        "for software testing only and are not medical diagnoses."
        if "synthetic_test" in sources
        else "Experimental model; predictions are not medical diagnoses."
    )
    (model_dir / "model_metadata.json").write_text(
        json.dumps({"training_data_notice": notice}, indent=2), encoding="utf-8"
    )

    report = classification_report(
        y_test,
        predictions,
        labels=list(range(len(encoder_classes))),
        target_names=encoder_classes,
        output_dict=True,
        zero_division=0,
    )
    return {
        "classes": encoder_classes,
        "sample_count": len(sequences),
        "report": report,
        "model_path": model_dir / "random_forest.pkl",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DISEASES_DIR)
    parser.add_argument("--model-dir", type=Path, default=MODEL_DIR)
    parser.add_argument(
        "--allow-synthetic-test-data",
        action="store_true",
        help="Explicitly allow training a non-clinical demonstration model.",
    )
    args = parser.parse_args()

    try:
        result = train_model(
            args.data_dir,
            args.model_dir,
            allow_synthetic_test_data=args.allow_synthetic_test_data,
        )
    except (ImportError, MultidiseaseTrainingError, OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Trained classes: {', '.join(result['classes'])}")
    print(f"Samples: {result['sample_count']}")
    print(f"Saved model: {result['model_path']}")
    print("Evaluation metrics are for synthetic test fixtures, not clinical performance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())