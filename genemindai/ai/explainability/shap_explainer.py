#!/usr/bin/env python3
"""
SHAP model prediction explainability for Beta Thalassemia classification.

Loads the trained Random Forest model, computes TreeExplainer SHAP feature
attributions from the k-mer feature dataset, and generates summary and bar plots
saved to reports/.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Tuple

import joblib
import matplotlib

matplotlib.use("Agg")  # Headless backend for CLI compatibility
import matplotlib.pyplot as plt
import pandas as pd
import shap

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_MODEL_PATH: Path = (
    PROJECT_ROOT / "ai" / "models" / "random_forest.pkl"
)
DEFAULT_DATASET_PATH: Path = (
    PROJECT_ROOT / "dataset" / "processed" / "expanded_feature_dataset.csv"
)
DEFAULT_REPORTS_DIR: Path = PROJECT_ROOT / "reports"


class SHAPExplainerError(Exception):
    """Raised when model loading, data loading, or SHAP calculation fails."""


def load_model_and_features(
    model_path: Path = DEFAULT_MODEL_PATH,
    csv_path: Path = DEFAULT_DATASET_PATH,
) -> Tuple[object, pd.DataFrame, pd.Series]:
    """
    Load saved model and feature dataset, separating features from target label.

    Args:
        model_path: Path to serialized model .pkl file.
        csv_path: Path to input feature dataset CSV.

    Returns:
        Tuple of (model, features_dataframe, label_series).

    Raises:
        SHAPExplainerError: If model or CSV file is missing or unparseable.
    """
    if not model_path.is_file():
        raise SHAPExplainerError(
            f"Model file not found: {model_path.resolve()}"
        )

    if not csv_path.is_file():
        raise SHAPExplainerError(
            f"Dataset file not found: {csv_path.resolve()}"
        )

    try:
        model = joblib.load(model_path)
    except Exception as exc:
        raise SHAPExplainerError(
            f"Failed to load model from {model_path}: {exc}"
        ) from exc

    try:
        df = pd.read_csv(csv_path)
    except Exception as exc:
        raise SHAPExplainerError(
            f"Failed to read CSV dataset from {csv_path}: {exc}"
        ) from exc

    if "label" not in df.columns:
        raise SHAPExplainerError(
            f"Target column 'label' missing from {csv_path}"
        )

    metadata_cols = {"id", "label", "mutation_name", "mutation_type"}
    feature_cols = [col for col in df.columns if col not in metadata_cols]

    if not feature_cols:
        raise SHAPExplainerError("No feature columns found in dataset.")

    X = df[feature_cols]
    y = df["label"]

    return model, X, y


def generate_shap_explanations(
    model: object,
    X: pd.DataFrame,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
) -> Tuple[Path, Path]:
    """
    Compute SHAP values with TreeExplainer and save summary and bar plots.

    Args:
        model: Trained tree-based model (RandomForestClassifier).
        X: DataFrame of feature inputs.
        reports_dir: Destination directory for saved plot images.

    Returns:
        Tuple of (summary_plot_path, bar_plot_path).

    Raises:
        SHAPExplainerError: If SHAP value calculation or plot saving fails.
    """
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_plot_path = reports_dir / "shap_summary.png"
    bar_plot_path = reports_dir / "shap_bar.png"

    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(X)
    except Exception as exc:
        raise SHAPExplainerError(
            f"Failed to compute SHAP values: {exc}"
        ) from exc

    # Handle 3D array vs list output for binary classification in SHAP
    if getattr(shap_values, "ndim", 0) == 3:
        target_shap = shap_values[:, :, 1]
    elif isinstance(shap_values, list) and len(shap_values) > 1:
        target_shap = shap_values[1]
    else:
        target_shap = shap_values

    # 1. Summary Plot (Beeswarm / Dot)
    try:
        plt.figure(figsize=(10, 6))
        shap.summary_plot(target_shap, X, show=False)
        plt.tight_layout()
        plt.savefig(summary_plot_path, bbox_inches="tight", dpi=300)
        plt.close()
    except Exception as exc:
        raise SHAPExplainerError(
            f"Failed to generate SHAP summary plot: {exc}"
        ) from exc

    # 2. Bar Plot
    try:
        plt.figure(figsize=(10, 6))
        shap.summary_plot(target_shap, X, plot_type="bar", show=False)
        plt.tight_layout()
        plt.savefig(bar_plot_path, bbox_inches="tight", dpi=300)
        plt.close()
    except Exception as exc:
        raise SHAPExplainerError(
            f"Failed to generate SHAP bar plot: {exc}"
        ) from exc

    return summary_plot_path, bar_plot_path


def run_explainability(
    model_path: Path = DEFAULT_MODEL_PATH,
    csv_path: Path = DEFAULT_DATASET_PATH,
    reports_dir: Path = DEFAULT_REPORTS_DIR,
) -> Tuple[Path, Path]:
    """
    Execute full SHAP explainability workflow and print results.

    Args:
        model_path: Path to serialized model file.
        csv_path: Path to input feature dataset.
        reports_dir: Path to output reports directory.

    Returns:
        Tuple of output file paths (summary_plot_path, bar_plot_path).
    """
    model, X, y = load_model_and_features(model_path, csv_path)

    model_name = type(model).__name__
    print(f"Model loaded: {model_name}")
    print(f"Dataset size: {X.shape}")
    print(f"Number of features: {X.shape[1]}")

    summary_path, bar_path = generate_shap_explanations(model, X, reports_dir)

    print(
        f"Output files:\n"
        f"  - {summary_path.resolve()}\n"
        f"  - {bar_path.resolve()}"
    )
    return summary_path, bar_path


def main() -> int:
    """
    Entry point for SHAP explainability script.

    Returns:
        0 on success, 1 on error.
    """
    try:
        run_explainability()
        return 0
    except SHAPExplainerError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
